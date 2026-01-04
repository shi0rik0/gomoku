import functools
import inspect
import logging
import os
from pathlib import Path
from typing import Optional

import fastapi.params
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from pydantic.alias_generators import to_camel

logger = logging.getLogger(__name__)


def snake_to_kebab(name: str) -> str:
    """Convert snake_case to kebab-case: get_game_state -> get-game-state"""
    return name.replace("_", "-")


def create_get_handler_with_signature(original_handle):
    """
    Dynamically create a handler function whose parameters are automatically
    converted to FastAPI Query parameters with camelCase aliases.
    """
    sig = inspect.signature(original_handle)
    new_params = []

    for param_name, param in sig.parameters.items():
        alias_name = to_camel(param_name)
        if param.default is inspect.Parameter.empty:
            # Required query parameter
            new_param = param.replace(default=Query(..., alias=alias_name))
        elif isinstance(param.default, fastapi.params.Depends):
            # Dependency injection, keep as is
            new_param = param
        else:
            # Optional query parameter
            new_param = param.replace(default=Query(param.default, alias=alias_name))
        new_params.append(new_param)

    new_signature = sig.replace(parameters=new_params)

    async def dynamic_handler(**kwargs):
        try:
            return await original_handle(**kwargs)
        except Exception as e:
            # You may want to log `endpoint_path` here for debugging
            raise HTTPException(400, str(e))

    # Apply the new signature so FastAPI can inspect it correctly
    dynamic_handler.__signature__ = new_signature  # type: ignore
    functools.update_wrapper(dynamic_handler, original_handle)
    return dynamic_handler


def load_api_routes(api_dir: Path, project_root: Path, base_prefix: str) -> APIRouter:
    """
    Automatically load API endpoints from Python files under `api_dir`.

    Conventions:
    - File: api/get_state.py → POST /api/get-state (default)
    - To make it GET: define `METHOD = "GET"` in the file
    - For GET: define `async def handle(param1: str, param2: int = 0) -> Response`
    - For POST: define `Request` (Pydantic model) and `async def handle(request: Request) -> Response`
    - Define `Response` Pydantic model for both
    """
    main_router = APIRouter()

    for py_file in api_dir.rglob("*.py"):
        if py_file.name.startswith("_") or py_file.name == "api_loader.py":
            continue

        try:
            # Compute endpoint path from file path
            rel_path = py_file.relative_to(api_dir)
            kebab_parts = [snake_to_kebab(p) for p in rel_path.with_suffix("").parts]
            endpoint_path = base_prefix + "/" + "/".join(kebab_parts)

            # Import module
            rel_module = py_file.relative_to(project_root)
            module_str = str(rel_module.with_suffix("")).replace(os.sep, ".")
            loaded_module = __import__(module_str, fromlist=[""])

            method = getattr(loaded_module, "METHOD", "POST").upper()
            ResponseModel = getattr(loaded_module, "Response", None)

            if ResponseModel is None:
                no_response_model = getattr(loaded_module, "NO_RESPONSE_MODEL", False)
                if not no_response_model:
                    logger.warning(
                        f"在 {module_str} 中未定义 Response 模型。可以通过指定 NO_RESPONSE_MODEL = True 来忽略此警告。"
                    )

            handle_func = getattr(loaded_module, "handle")

            if method == "GET":
                handler = create_get_handler_with_signature(handle_func)
                main_router.add_api_route(
                    endpoint_path,
                    handler,
                    methods=["GET"],
                    response_model=ResponseModel,
                )
            else:  # POST
                main_router.add_api_route(
                    endpoint_path,
                    handle_func,
                    methods=["POST"],
                    response_model=ResponseModel,
                )

            logger.info(f"已注册 {method} {endpoint_path}")

        except Exception as e:
            logger.error(f"无法加载 {py_file}", exc_info=True)
            raise

    return main_router
