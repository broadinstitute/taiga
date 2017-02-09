import flask
import re
import logging

# There are a few ways we could get a user_id depending on the app's config
#
# config['TAKE_USER_ID_FROM_HEADER'] set to the name of a header property on the request.
#    oauth2_proxy appears to set X-Forwarded-User and GAP-Auth to the user id
#    if authentication were successful.
#
# config['BEARER_TOKEN_LOOKUP'] if set, will call this as a function, when a request with
#    a "Authorization" header arrives to get the user_id.   Function should return None if
#    token is not valid.  This will mostly be useful for bearer tokens provided on API requests
#
# config['DEFAULT_USER_ID'] set to the user id to return.  Should only be used in dev/debugging
#

log = logging.getLogger(__name__)


def get_user_id():
    return flask.g._user_id


def init_auth(app):
    app.before_request(update_user_info)


def update_user_info():
    import taiga2.controllers.models_controller as mc
    request = flask.request
    config = flask.current_app.config
    user_id = None

    # Use for development environment
    # user_name_header_name = config.get("TAKE_USER_NAME_FROM_HEADER", None)
    # user_email_header_name = config.get("TAKE_USER_EMAIL_FROM_HEADER", None)
    bearer_token_lookup = config.get("BEARER_TOKEN_LOOKUP", None)
    default_user_id = config.get("DEFAULT_USER_ID", None)

    # Use for production environment
    user_name_header_name = flask.request.headers['X-Forwarded-User']
    user_email_header_name = flask.request.headers['X-Forwarded-Email']

    if user_id is None and bearer_token_lookup is not None:
        print("We are in bearer_tolent_lookup!")
        authorization = request.headers.get('Authorization')
        if authorization is not None:
            m = re.match("Bearer (\\S+)", authorization)
            if m is not None:
                token = m.group(1)
                user_id = bearer_token_lookup(token)
                log.debug("Got token %s which mapped to user %s", token, user_id)
            else:
                log.warn("Authorization header malformed: %s", authorization)

    if user_name_header_name is not None or user_email_header_name is not None:
        # user_id = request.headers.get(user_id_header_name)
        try:
            user = mc.get_user_by_name(user_name_header_name)
            # TODO: This should never happen, but not sure what is the best: fetch by email or fetch by name (which is extracted from email by Oauth_prox)
            user = mc.get_user_by_email(user_email_header_name)
        except:
            # User does not exists so we can create it
            user = mc.add_user(name=user_name_header_name,
                               email=user_email_header_name)
            print("We just created the user {} with email {}".format(user_name_header_name, user_email_header_name))
            print("Check of the user name ({}) and email ({})".format(user.name, user.email))
        user_id = user.id
        log.debug("Looked up header field user_name %s and user_email %s to find username: %s",
                  user_name_header_name,
                  user_email_header_name,
                  user_id)

    if user_id is None and default_user_id is not None:
        user_id = default_user_id

    flask.g.current_user = user

    return None
