import json
import matplotlib.pyplot as plt
from turtle_env import TurtleEnv

env = TurtleEnv()
num_episodes = 5
max_steps = env.max_steps

all_rewards = []
interaction_logs = []

for episode in range(num_episodes):
    state = env.reset()
    episode_rewards = []

    for step in range(max_steps):
        action = env.action_space.sample()  # random policy
        next_state, reward, done, _ = env.step(action)

        feedback = {
            "sentiment": next_state[10],    # or wherever you store it
            "engagement": next_state[11] 
        }
        interaction_logs.append({
            "episode": episode,
            "step": step,
            "action": int(action),
            "reward": float(reward),
            "sentiment": float(feedback["sentiment"]),
            "engagement": float(feedback["engagement"]),
        })

        episode_rewards.append(reward)
        state = next_state
        if done:
            break

    total_reward = sum(episode_rewards)
    all_rewards.append(total_reward)
    print(f"Episode {episode+1} - Total Reward: {total_reward}")

# Save to JSON
with open("interaction_logs.json", "w") as f:
    json.dump(interaction_logs, f)

# Plot total reward per episode
plt.plot(all_rewards, marker='o')
plt.title("Total Reward per Episode")
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.show()
