# Copyright (c) 2015 Aptira Pty Ltd.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Policy Engine For Guts"""


from oslo_config import cfg
from oslo_policy import opts as policy_opts
from oslo_policy import policy

from guts import exception

CONF = cfg.CONF
policy_opts.set_defaults(cfg.CONF, 'policy.json')

_ENFORCER = None


def init():
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF)


def enforce_action(context, action):
    """Checks that the action can be done by the given context.

    Applies a check to ensure the context's project_id and user_id can be
    applied to the given action using the policy enforcement api.
    """

    return enforce(context, action, {'project_id': context.project_id,
                                     'user_id': context.user_id})


def enforce(context, action, target):
    """Verifies that the action is valid on the target in this context.

       :param context: guts context
       :param action: string representing the action to be checked
           this should be colon separated for clarity.

       :param object: dictionary representing the object of the action
           for object creation this should be a dictionary representing the
           location of the object e.g. ``{'project_id': context.project_id}``

       :raises PolicyNotAuthorized: if verification fails.

    """
    init()

    return _ENFORCER.enforce(action, target, context.to_dict(),
                             do_raise=True,
                             exc=exception.PolicyNotAuthorized,
                             action=action)


def check_is_admin(roles, context=None):
    """Whether or not user is admin according to policy setting.

       Can use roles or user_id from context to determine if user is admin.
       In a multi-domain configuration, roles alone may not be sufficient.
    """
    init()

    # include project_id on target to avoid KeyError if context_is_admin
    # policy definition is missing, and default admin_or_owner rule
    # attempts to apply.  Since our credentials dict does not include a
    # project_id, this target can never match as a generic rule.
    target = {'project_id': ''}
    if context is None:
        credentials = {'roles': roles}
    else:
        credentials = {'roles': context.roles,
                       'user_id': context.user_id
                       }

    return _ENFORCER.enforce('context_is_admin', target, credentials)
