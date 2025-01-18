import os
import json
import numpy as np
import gym
from gym import spaces

class TurtleEnv(gym.Env):
    """
    A conversational environment that:
      - Loads/stores user profile with personality
      - Tracks sentiment & engagement
      - Applies action-dependent feedback shaped by personality
      - Applies repeated-action penalty (scaled)
      - Applies a final bonus for average sentiment/engagement
      - Has optional diminishing returns as sentiment/engagement approach 1.0
    """
    def __init__(
        self,
        user_id="default_user",
        user_profile_path="user_profile.json",
        max_steps=30
    ):
        super().__init__()

        # We'll use a 28-dim state:
        #   10-d conversation context
        #    2-d sentiment, engagement
        #    5-d personality
        #    5-d one-hot last action
        #    1-d step ratio
        #    5-d user_interests or placeholders
        # shape: 10 + 2 + 5 + 5 + 1 + 5 = 28
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(28,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(5)  # actions: 0..4

        self.user_id = user_id
        self.user_profile_path = user_profile_path
        self.max_steps = max_steps

        self.user_profile = self._load_user_profile()
        self.reset()

    # -------------------------------------------------------------------------
    #                        PERSISTENCE (USER PROFILE)
    # -------------------------------------------------------------------------
    def _load_user_profile(self):
        """Load or create a user profile from disk. 
        Must contain 'personality' or we'll default it."""
        if os.path.exists(self.user_profile_path):
            with open(self.user_profile_path, "r") as f:
                data = json.load(f)
            if self.user_id in data:
                return data[self.user_id]

        # If we get here, create a default profile
        profile = {
            # personality = [extroversion, humor_pref, patience, knowledge, random_factor]
            "personality": list(np.random.uniform(0.0, 1.0, size=(5,))),
            "times_chatted": 0
        }
        self._save_user_profile(profile)
        return profile

    def _save_user_profile(self, profile_data=None):
        """Save/append user profile to disk, keyed by user_id."""
        if profile_data is None:
            profile_data = self.user_profile

        if os.path.exists(self.user_profile_path):
            with open(self.user_profile_path, "r") as f:
                data = json.load(f)
        else:
            data = {}

        data[self.user_id] = profile_data

        with open(self.user_profile_path, "w") as f:
            json.dump(data, f, indent=2)

    # -------------------------------------------------------------------------
    #                                 ENV LOGIC
    # -------------------------------------------------------------------------
    def reset(self):
        self.current_step = 0
        self.user_profile = self._load_user_profile()  # refresh from disk if changed

        # sentiment & engagement start at 0.5
        self.sentiment = 0.5
        self.engagement = 0.5

        # personality from user profile
        self.personality = np.array(self.user_profile["personality"], dtype=np.float32)

        # repeated actions tracking
        self.last_action = -1
        self.consecutive_action_count = 0

        # track cumulative for final bonus
        self.cumulative_sentiment = 0.0
        self.cumulative_engagement = 0.0

        self.state = self._build_state(action=None)
        return self.state

    def step(self, action):
        self.current_step += 1

        # user feedback
        new_s, new_e = self._simulate_user_feedback(action)

        self.sentiment = new_s
        self.engagement = new_e

        # accumulate for final bonus
        self.cumulative_sentiment += new_s
        self.cumulative_engagement += new_e

        # immediate reward
        reward = self._calculate_reward(action)

        # build next state
        self.state = self._build_state(action)

        # check done
        done = (self.current_step >= self.max_steps)
        if done:
            # final bonus
            avg_s = self.cumulative_sentiment / self.max_steps
            avg_e = self.cumulative_engagement / self.max_steps
            # Weighted final bonus. Example: 0.3 for immediate + 0.7 for final average
            final_bonus = 0.7 * (0.5 * avg_s + 0.5 * avg_e)
            reward += final_bonus

            self.user_profile["times_chatted"] += 1
            # optionally adjust personality or store stats
            self._save_user_profile()

        return self.state, reward, done, {}

    # -------------------------------------------------------------------------
    #                                STATE BUILDING
    # -------------------------------------------------------------------------
    def _build_state(self, action):
        # conversation context (random for demonstration)
        context = np.random.uniform(-0.5, 0.5, size=(10,))

        # last action (one-hot)
        if action is None:
            action_onehot = np.zeros(5, dtype=np.float32)
        else:
            action_onehot = np.zeros(5, dtype=np.float32)
            action_onehot[action] = 1.0

        # step ratio
        step_ratio = np.array([self.current_step / self.max_steps], dtype=np.float32)

        # personality is 5-d
        se = np.array([self.sentiment, self.engagement], dtype=np.float32)

        # optional placeholders (5-d interests)
        user_interests = np.zeros(5, dtype=np.float32)

        combined = np.concatenate([
            context,         # shape (10,)
            se,             # shape (2,)
            self.personality,  # shape (5,)
            action_onehot,  # shape (5,)
            step_ratio,     # shape (1,)
            user_interests  # shape (5,) 
        ])
        return combined.astype(np.float32)

    # -------------------------------------------------------------------------
    #                           USER FEEDBACK SIMULATION
    # -------------------------------------------------------------------------
    def _simulate_user_feedback(self, action):
        """
        More dynamic, personality-based, with diminishing returns if sentiment/engagement 
        are already high (so we don't saturate too quickly).
        """
        (extroversion, humor_pref, patience, knowledge, randomness) = self.personality

        base_s = self.sentiment
        base_e = self.engagement

        # action-based base changes
        if action == 0:   # greet
            ds = np.random.uniform(0.0, 0.03) * (1 + 0.5 * extroversion)
            de = np.random.uniform(-0.01, 0.04) * (1 + 0.5 * extroversion)
        elif action == 1: # ask question
            ds = np.random.uniform(-0.01, 0.02) * (1 + 0.3 * knowledge)
            de = np.random.uniform(0.0, 0.1)    * (1 + 0.3 * extroversion)
        elif action == 2: # statement
            ds = np.random.uniform(-0.02, 0.02) * (1 + 0.2 * knowledge)
            de = np.random.uniform(-0.02, 0.02) * (1 + 0.2 * knowledge)
        elif action == 3: # joke
            ds = np.random.uniform(-0.05, 0.1) * (1 + 0.7 * humor_pref)
            de = np.random.uniform(-0.05, 0.05) * (1 + 0.4 * extroversion)
        else:  # action == 4: conclude
            ds = np.random.uniform(-0.05, 0.01) * (1 + 0.1 * patience)
            de = np.random.uniform(-0.1, 0.0)   * (1 + 0.1 * patience)

        # add randomness factor
        ds *= (1 + 0.3 * randomness)
        de *= (1 + 0.3 * randomness)

        # optional diminishing returns if close to 1.0
        # e.g. scale changes by (1 - current_value) so you don't saturate quickly
        ds *= (1.0 - base_s)
        de *= (1.0 - base_e)

        new_s = np.clip(base_s + ds, 0.0, 1.0)
        new_e = np.clip(base_e + de, 0.0, 1.0)

        return new_s, new_e

    # -------------------------------------------------------------------------
    #                              REWARD FUNCTION
    # -------------------------------------------------------------------------
    def _calculate_reward(self, action):
        """
        Weighted immediate reward = 0.6*engagement + 0.4*sentiment.
        Includes scaled repeated-action penalty & stronger early-conclusion penalty.
        """
        # immediate reward
        reward = 0.6 * self.engagement + 0.4 * self.sentiment

        # repeated-action penalty
        if action == self.last_action:
            self.consecutive_action_count += 1
        else:
            self.consecutive_action_count = 0

        # scale penalty for each extra repeated step beyond 2
        # e.g. if repeated 3 times in a row, penalty= -0.3; 4 times= -0.5, etc.
        repeats_beyond_two = max(0, self.consecutive_action_count - 2)
        if repeats_beyond_two > 0:
            penalty = 0.2 + 0.2 * (repeats_beyond_two - 1)  # 3 in a row= -0.2, 4= -0.4, etc.
            reward -= penalty

        # early conclusion penalty: 
        # if action=4 with more than ~5 steps left, we penalize more strongly
        # example: -0.8 if concluding with >5 steps left
        if action == 4:
            steps_left = self.max_steps - self.current_step
            if steps_left > 5:
                reward -= 0.8

        self.last_action = action
        return reward
