import os
import subprocess
import sys

from redash.query_runner import *


class Script(BaseQueryRunner):
    @classmethod
    def annotate_query(cls):
        return False

    @classmethod
    def enabled(cls):
        return "check_output" in subprocess.__dict__

    @classmethod
    def configuration_schema(cls):
        return {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'title': 'Scripts path'
                },
                'shell': {
                    'type': 'boolean',
                    'title': 'Execute command through the shell'
                }
            },
            'required': ['path']
        }

    @classmethod
    def type(cls):
        return "insecure_script"

    def __init__(self, configuration):
        super(Script, self).__init__(configuration)

        # If path is * allow any execution path
        if self.configuration["path"] == "*":
            return

        # Poor man's protection against running scripts from outside the scripts directory
        if self.configuration["path"].find("../") > -1:
            raise ValueError("Scripts can only be run from the configured scripts directory")

    def test_connection(self):
        pass

    def run_query(self, query, user):
        try:
            script = query

            if self.configuration["path"] != "*":
                script = os.path.join(self.configuration["path"], query.split(" ")[0])
                if not os.path.exists(script):
                    return None, "Script '%s' not found in script directory" % query

                script = os.path.join(self.configuration["path"], query).split(" ")

            output = subprocess.check_output(script, shell=self.configuration['shell'])
            if output is not None:
                output = output.strip()
                if output != "":
                    return output, None

            return None, "Error reading output"
        except subprocess.CalledProcessError as e:
            return None, str(e)
        except KeyboardInterrupt:
            return None, "Query cancelled by user."
        except Exception:
            raise sys.exc_info()[1], None, sys.exc_info()[2]


register(Script)
