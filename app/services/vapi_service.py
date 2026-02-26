import requests
from loguru import logger

from app.config import get_settings
from app.utils.vapi import TOOLS, VAPI_BASE_URL

HEADERS = {
    "Authorization": f"Bearer {get_settings().VAPI_API_TOKEN}",
    "Content-Type": "application/json",
}

ASSISTANT_ID = get_settings().ASSISTANT_ID


def list_tools():
    r = requests.get(f"{VAPI_BASE_URL}/tool", headers=HEADERS, timeout=30)
    data = r.json()
    logger.debug("VAPI list_tools response: {}", data)
    return data


def upsert_tool(tool_payload: dict) -> str:
    existing = list_tools()
    found = next((t for t in existing if t.get("name") == tool_payload.get("name")), None)

    if found:
        tool_id = found["id"]
        logger.info("Updating tool: {} ({})", tool_payload.get("name"), tool_id)
        r = requests.patch(
            f"{VAPI_BASE_URL}/tool/{tool_id}",
            headers=HEADERS,
            json=tool_payload,
            timeout=30,
        )
        logger.debug("VAPI patch tool response: {}", r.json())
        return tool_id

    logger.info("Creating tool: {}", tool_payload.get("name"))
    r = requests.post(
        f"{VAPI_BASE_URL}/tool",
        headers=HEADERS,
        json=tool_payload,
        timeout=30,
    )
    data = r.json()
    logger.debug("VAPI create tool response: {}", data)
    return data.get("id")


def get_assistant():
    r = requests.get(f"{VAPI_BASE_URL}/assistant/{ASSISTANT_ID}", headers=HEADERS, timeout=30)
    data = r.json()
    logger.debug("VAPI get_assistant response: {}", data)
    return data


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
    logger.debug("VAPI attach_tools response: {}", r.json())
    return r.json()


def main():
    tool_ids = []
    for tool in TOOLS:
        tool_id = upsert_tool(tool)
        tool_ids.append(tool_id)

    logger.info("Attaching tools to assistant...")
    attach_tools(tool_ids)
    logger.info("Tools created/updated and attached. Tool IDs: {}", tool_ids)


if __name__ == "__main__":
    main()
