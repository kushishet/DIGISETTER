import requests

LM_STUDIO_URL = "http://192.168.29.140:1234/v1/chat/completions"

MODEL_NAME = "mistral-7b-instruct-v0.1"

def call_chatgpt(prompt, role="examiner", temperature=0.7, max_tokens=4096):
    """
    Calls a local Mistral model via LM Studio's HTTP API.
    Returns only the content of the assistant message.
    Raises exceptions if response is invalid or fails.
    """
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"You are an {role} generating academic exam questions."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(LM_STUDIO_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()

        # Validate expected structure
        if "choices" not in result or not result["choices"]:
            raise ValueError("LLM response missing 'choices' or is empty.")

        content = result["choices"][0]["message"]["content"]
        if not content or not isinstance(content, str):
            raise ValueError("LLM response does not contain valid message content.")

        return content

    except requests.exceptions.Timeout:
        raise Exception("LLM request timed out (120s).")

    except requests.exceptions.ConnectionError:
        raise Exception("Connection to LM Studio failed. Is it running on port 1234?")

    except requests.exceptions.RequestException as e:
        raise Exception(f"LLM request error: {str(e)}")

    except ValueError as e:
        raise Exception(f"Invalid LLM response structure: {str(e)}")

    except Exception as e:
        raise Exception(f"Unexpected failure in call_chatgpt(): {str(e)}")