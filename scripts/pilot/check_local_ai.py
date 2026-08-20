#!/usr/bin/env python3
"""Report whether the pilot's local speech and extraction services are ready."""

from __future__ import annotations

import json

from smartcoat.api.routes.lab_capture_ai import build_preflight_response


def main() -> int:
    result = build_preflight_response()
    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0 if result.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
