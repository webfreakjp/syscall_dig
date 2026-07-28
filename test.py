import ctypes
import json
import os
import sys
import traceback


INPUTS_FILE = os.environ.get(
    "SYSCALL_DIG_INPUTS_FILE",
    "/syscall-dig-inputs.json",
)
with open(INPUTS_FILE, encoding="utf-8") as inputs_file:
    syscall_dig_inputs = inputs_file.read()

enable_network_value = os.environ.get(
    "SYSCALL_DIG_ENABLE_NETWORK",
    "true",
).lower()
if enable_network_value not in {"true", "false"}:
    raise ValueError(
        "SYSCALL_DIG_ENABLE_NETWORK must be either true or false."
    )
enable_network = enable_network_value == "true"


# setup sys.excepthook
def excepthook(type, value, tb):
    sys.stderr.write("".join(traceback.format_exception(type, value, tb)))
    sys.stderr.flush()
    sys.exit(-1)


sys.excepthook = excepthook

lib = ctypes.CDLL("/var/sandbox/sandbox-python/python.so")
lib.DifySeccomp.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_bool]
lib.DifySeccomp.restype = None

os.chdir("/var/sandbox/sandbox-python")

lib.DifySeccomp(65537, 1001, enable_network)


# User code starts here.

import json
from typing import Any


def main(box_response_body: str) -> dict:
    """
    Box APIのレスポンスからMarkdown representationの状態と
    ダウンロードURLを取得する。

    想定するBox API:
        GET /2.0/files/{file_id}?fields=id,name,representations

    必須ヘッダー:
        X-Rep-Hints: [markdown]

    Args:
        box_response_body:
            Box APIを呼び出したHTTPリクエストノードのbody。
            JSON文字列として渡す。

    Returns:
        Dify Codeノード用の出力辞書。
    """

    result = {
        "ready": False,
        "status": "",
        "download_url": "",
        "info_url": "",
        "file_id": "",
        "file_name": "",
        "error": "",
    }

    # HTTPノードのbodyをJSONとして解析
    try:
        box_response: dict[str, Any] = json.loads(box_response_body)
    except (TypeError, json.JSONDecodeError) as exc:
        result["error"] = (
            "Box APIレスポンスをJSONとして解析できません: "
            f"{exc}"
        )
        return result

    result["file_id"] = str(box_response.get("id", ""))
    result["file_name"] = str(box_response.get("name", ""))

    entries = (
        box_response
        .get("representations", {})
        .get("entries", [])
    )

    if not isinstance(entries, list):
        result["error"] = (
            "representations.entriesが配列ではありません。"
        )
        return result

    # Markdown representationを検索
    markdown_entry = None

    for entry in entries:
        if (
            isinstance(entry, dict)
            and entry.get("representation") == "markdown"
        ):
            markdown_entry = entry
            break

    if markdown_entry is None:
        result["error"] = (
            "Markdown representationがレスポンスに"
            "含まれていません。"
            "X-Rep-Hints: [markdown]を指定しているか、"
            "対象ファイル形式が対応しているか確認してください。"
        )
        return result

    status = str(
        markdown_entry
        .get("status", {})
        .get("state", "")
    )

    info_url = str(
        markdown_entry
        .get("info", {})
        .get("url", "")
    )

    result["status"] = status
    result["info_url"] = info_url

    # 未生成の場合、info_urlを別のHTTPノードで呼び出す
    if status == "none":
        result["error"] = (
            "Markdown representationはまだ生成されていません。"
            "info_urlをHTTPリクエストノードでGETしてください。"
        )
        return result

    # 生成処理中
    if status in {"pending", "viewable"}:
        result["error"] = (
            "Markdown representationは生成中です。"
            f"現在の状態: {status}"
        )
        return result

    if status != "success":
        result["error"] = (
            "想定外のrepresentation状態です: "
            f"{status}"
        )
        return result

    url_template = str(
        markdown_entry
        .get("content", {})
        .get("url_template", "")
    )

    if not url_template:
        result["error"] = (
            "content.url_templateがありません。"
        )
        return result

    # Markdownは非ページ形式なのでasset_pathは空にする
    download_url = url_template.replace(
        "{+asset_path}",
        "",
    )

    return {
        "ready": True,
        "status": status,
        "download_url": download_url,
        "info_url": info_url,
        "file_id": result["file_id"],
        "file_name": result["file_name"],
        "error": "",
    }

# User code ends here.

from json import dumps, loads

# execute main function, and return the result
inputs = loads(syscall_dig_inputs)
if not isinstance(inputs, dict):
    raise TypeError("The syscall test inputs must be a JSON object.")
output = main(**inputs)

# convert output to json and print
output = dumps(output, indent=4)

result = f"""<<RESULT>>
{output}
<<RESULT>>"""

print(result)
