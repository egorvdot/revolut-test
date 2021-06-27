import os
import secrets
from typing import List, Any

import uvicorn

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel
from starlette import status

from nest import FlatDicts, RecursiveFlatDictsTransformation, RecursiveFlatDictsTransformationError, transformations_map


class AuthenticationChecking:
    """Check correctness of credentials."""

    def __init__(self):
        self._username = os.environ.get('TRANSFORMATION_USERNAME', 'codelock')
        self._password = os.environ.get('TRANSFORMATION_PASSWORD', 'iloveyou')

    def is_correct(self, username: str, password: str) -> bool:
        """Safety checks credentials.

        Block timing attacks.
        https://fastapi.tiangolo.com/advanced/security/http-basic-auth/#timing-attacks
        """
        correct_username = secrets.compare_digest(username, self._username)
        correct_password = secrets.compare_digest(password, self._password)

        return correct_username and correct_password


app = FastAPI()
security = HTTPBasic()
create_transformation = RecursiveFlatDictsTransformation.create
authentication = AuthenticationChecking()


class TransformationRequest(BaseModel):
    """Data and conditions for transformation."""

    flat_dicts: FlatDicts
    nesting_levels: List[str]
    use_recursive_realization: bool = False

    class Config:
        schema_extra = {
            'example': {
                'flat_dicts': [
                    {
                        'currency': 'GBP',
                        'country': 'UK',
                        'amount': 100,
                    },
                    {
                        'currency': 'RUR',
                        'country': 'RUS',
                        'amount': 100,
                    },
                ],
                'nesting_levels': [
                    'currency',
                    'country',
                ]
            }
        }


class Message(BaseModel):
    """Response format for errors."""

    detail: Any


@app.put(
    '/transformation',
    responses={
        200: {
            'description': 'Item requested by ID',
            'content': {
                'application/json': {
                    'example': {'GBP': {'UK': {'amount': 100}}, 'RUR': {'RUS': {'amount': 1}}}
                },
            },
        },
        400: {
            'model': Message,
            'description': 'Bad request',
            'content': {
                'application/json': {
                    'example': {'detail': '[]: empty nesting levels'}
                },
            },
        },
        401: {
            'model': Message,
            'description': 'Bad request',
            'content': {
                'application/json': {
                    'example': {'detail': 'Incorrect username or password'}
                },
            },
        },
        422: {
            'model': Message,
            'description': 'Bad request',
            'content': {
                'application/json': {
                    'example': {
                        'detail': [{
                            'loc': [
                                'body',
                                'nesting_levels'
                            ],
                            'msg': 'field required',
                            'type': 'value_error.missing',
                        }],
                    }
                },
            },
        },
    },
)
async def put_transformation(
    request: TransformationRequest,
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Transform flat dicts to dict of dicts."""
    if not authentication.is_correct(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Basic'},
        )
    transformation_factory = transformations_map[request.use_recursive_realization]
    try:
        transformation = transformation_factory.create(
            nesting_levels=request.nesting_levels,
            flat_dicts=request.flat_dicts,
        )
        transformed = transformation()
    except RecursiveFlatDictsTransformationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{err.args[0]}:{err.args[1]}')
    return transformed


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', http='h11', loop='asyncio')
