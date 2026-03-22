import os
import requests
import subprocess

API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/o3-mini"

if not API_KEY:
    raise ValueError("请先设置 OPENROUTER_API_KEY 环境变量")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def load_agent_prompt():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "agent.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

agent_message = {
    "role": "system",
    "content": load_agent_prompt()
}

def load_skill_prompt():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "skill.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

skill_message = {
    "role": "system",
    "content": load_skill_prompt()
}


messages = [agent_message, skill_message]

def run_script(script: str) -> str:
    try:
        result = subprocess.run(
            script,
            shell=True,
            capture_output=True,
            text=True,
            timeout=20
        )
        return result.stdout or result.stderr or "(no output)"
    except Exception as e:
        return str(e)


try:
    with requests.Session() as session:
        while True:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit"}:
                print("Bye")
                break

            print("\n---------- Agent Start ----------")
            messages.append({"role": "user", "content": user_input})

            while True:
                response = session.post(
                    URL,
                    headers=headers,
                    json={
                        "model": MODEL,
                        "messages": messages,
                        "reasoning": {"effort": "medium"}
                    },
                    timeout=30
                )

                response.raise_for_status()
                data = response.json()

                assistant_text = data["choices"][0]["message"]["content"].strip()
                print("Agent:", assistant_text)

                messages.append({
                    "role": "assistant",
                    "content": assistant_text
                })

                if assistant_text.startswith("finish:"):
                    print("\n---------- Agent Finish ----------")
                    print(assistant_text)
                    break

                elif assistant_text.startswith("script:"):
                    script = assistant_text[len("script:"):].strip()

                    print("\n[Executing Script]")
                    print(script)

                    output = run_script(script)

                    print("\n[Script Output]")
                    print(output)

                    messages.append({
                        "role": "user",
                        "content": f"execute result:\n{output}"
                    })

                else:
                    print("⚠️ 格式错误，终止")
                    break

except KeyboardInterrupt:
    print("\nNerdbot: Bye and quit")
