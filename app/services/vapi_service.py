import requests
from app.utils.vapi import (TOOLS, VAPI_BASE_URL)
from app.config import get_settings

HEADERS = {
    "Authorization": f"Bearer {get_settings().VAPI_API_TOKEN}",
    "Content-Type": "application/json",
}

ASSISTANT_ID = get_settings().ASSISTANT_ID



def list_tools():
    r = requests.get(f"{VAPI_BASE_URL}/tool", headers=HEADERS, timeout=30)
    print(r.json())
    return r.json()


def upsert_tool(tool_payload: dict) -> str:
    existing = list_tools()
    found = next((t for t in existing if t.get("name") == tool_payload.get('name')), None)

    if found:
        tool_id = found["id"]
        print(f"Updating tool: {tool_payload.get('name')} ({tool_id})")
        r = requests.patch(
            f"{VAPI_BASE_URL}/tool/{tool_id}",
            headers=HEADERS,
            json=tool_payload,
            timeout=30,
        )
        print(r.json())
        return tool_id

    print(f"Creating tool: {tool_payload.get('name')}")
    r = requests.post(
        f"{VAPI_BASE_URL}/tool",
        headers=HEADERS,
        json=tool_payload,
        timeout=30,
    )
    print(r.json())
    return r.json().get("id")


def get_assistant():
    r = requests.get(f"{VAPI_BASE_URL}/assistant/{ASSISTANT_ID}", headers=HEADERS, timeout=30)
    print(r.json())
    return r.json()


def attach_tools(tool_ids: list[str]):
    assistant = get_assistant()

    # Preserve existing model config and only set toolIds
    model = assistant.get("model") or {}
    model["toolIds"] = tool_ids

    r = requests.patch(
        f"{VAPI_BASE_URL}/assistant/{ASSISTANT_ID}",
        headers=HEADERS,
        json={"model": model},
        timeout=30,
    )
    print(r.json())
    return r.json()


def main():
    tool_ids = []
    for tool in TOOLS:
        tool_id = upsert_tool(tool)
        tool_ids.append(tool_id)

    print("Attaching tools to assistant...")
    attach_tools(tool_ids)

    print("\nDONE ✅ Tools created/updated and attached.")
    print("Tool IDs:", tool_ids)


if __name__ == "__main__":
    main()
