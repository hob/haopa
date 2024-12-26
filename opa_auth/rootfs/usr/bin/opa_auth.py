#!/usr/bin/env python3
import os
import json
import logging
import requests
from aiohttp import web
import voluptuous as vol
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

OPTIONS_SCHEMA = vol.Schema({
    vol.Required('policy_path'): str,
    vol.Required('log_level'): vol.In(['trace', 'debug', 'info', 'warning', 'error'])
})

class OPAAuthorizationAddon:
    def __init__(self):
        self.options = self._get_options()
        self._setup_logging()
        self.supervisor_token = os.environ.get('SUPERVISOR_TOKEN')
        if not self.supervisor_token:
            _LOGGER.error("No supervisor token found")
            sys.exit(1)
        
        self.opa_url = "http://localhost:8181"
        
    def _get_options(self):
        options_path = "/data/options.json"
        with open(options_path) as file:
            options = json.load(file)
            
        try:
            return OPTIONS_SCHEMA(options)
        except vol.Invalid as err:
            _LOGGER.error("Invalid options: %s", err)
            sys.exit(1)
            
    def _setup_logging(self):
        log_level = getattr(logging, self.options['log_level'].upper())
        _LOGGER.setLevel(log_level)

    async def authorize_action(self, request):
        try:
            data = await request.json()
            
            entity_id = data.get('entity_id')
            action = data.get('action')
            user = data.get('user')
            
            if not all([entity_id, action, user]):
                return web.Response(
                    status=400,
                    text="Missing required fields: entity_id, action, or user"
                )

            input_data = {
                "input": {
                    "entity_id": entity_id,
                    "action": action,
                    "user": user,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            try:
                response = requests.post(
                    f"{self.opa_url}/v1/data/homeassistant/allow",
                    json=input_data,
                    timeout=5
                )
                response.raise_for_status()
                
                result = response.json()
                is_allowed = result.get("result", False)
                
                if is_allowed:
                    return web.Response(status=200, text="Authorized")
                else:
                    return web.Response(status=403, text="Not authorized")
                    
            except requests.exceptions.RequestException as err:
                _LOGGER.error("Failed to query OPA: %s", err)
                return web.Response(status=500, text="Authorization service unavailable")

        except Exception as err:
            _LOGGER.error("Error processing authorization request: %s", err)
            return web.Response(status=500, text="Internal server error")

    async def start_server(self):
        app = web.Application()
        app.router.add_post('/authorize', self.authorize_action)
        return app

async def main():
    addon = OPAAuthorizationAddon()
    app = await addon.start_server()
    return app

if __name__ == '__main__':
    web.run_app(main(), port=8099)