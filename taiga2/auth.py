import flask
import re
import logging

from sqlalchemy.orm.exc import NoResultFound

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


def init_front_auth(app):
    app.before_request(user_oauth_actions)


def user_oauth_actions():
    import taiga2.controllers.models_controller as mc
    request = flask.request
    config = flask.current_app.config
    user = None

    # Use for development environment
    # user_name_header_name = config.get("TAKE_USER_NAME_FROM_HEADER", None)
    # user_email_header_name = config.get("TAKE_USER_EMAIL_FROM_HEADER", None)
    bearer_token_lookup = config.get("BEARER_TOKEN_LOOKUP", None)
    default_user_email = config.get("DEFAULT_USER_EMAIL", None)

    # Use for production environment
    user_name_header_name = request.headers.get('X-Forwarded-User', None)
    user_email_header_name = request.headers.get('X-Forwarded-Email', None)

    if user_name_header_name is not None or user_email_header_name is not None:
        # user_id = request.headers.get(user_id_header_name)
        try:
            user = mc.get_user_by_name(user_name_header_name)
            # TODO: This should never happen, but not sure what is the best: fetch by email or fetch by name (which is extracted from email by Oauth_prox)
            user = mc.get_user_by_email(user_email_header_name)
        except NoResultFound:
            # User does not exists so we can create it
            user = mc.add_user(name=user_name_header_name,
                               email=user_email_header_name)
            log.debug("We just created the user {} with email {}".format(user_name_header_name, user_email_header_name))
            log.debug("Check of the user name ({}) and email ({})".format(user.name, user.email))
        user_id = user.id
        log.debug("Looked up header field user_name %s and user_email %s to find username: %s",
                  user_name_header_name,
                  user_email_header_name,
                  user_id)

    if user is None and default_user_email is not None:
        print("We did not find the user from the headers, loading the default user by its email {}" \
              .format(default_user_email))

        try:
            user = mc.get_user_by_email(default_user_email)
        except NoResultFound:
            import uuid
            user = mc.add_user(name=str(uuid.uuid4()),
                               email=default_user_email)

    flask.g.current_user = user

    return None


def init_backend_auth(app):
    app.before_request(from_bearer_set_current_user)


def from_bearer_set_current_user():
    import taiga2.controllers.models_controller as mc
    request = flask.request
    config = flask.current_app.config
    user = None
    bearer_token = request.headers.get("Authorization", None)
    # bearer_token_lookup = config.get("BEARER_TOKEN_LOOKUP", None)

    if user is None and bearer_token is not None:
        m = re.match("Bearer (\\S+)", bearer_token)
        if m is not None:
            token = m.group(1)
            user = bearer_token_lookup(token)
            log.debug("Got token %s which mapped to user %s", token, user.email)
        else:
            log.warn("Authorization header malformed: %s", bearer_token)
    else:
        # TODO: Should ask for returning a "Not authenticated" page/response number
        raise Exception("No user passed")
    flask.g.current_user = user


def bearer_token_lookup(token):
    import taiga2.controllers.models_controller as mc
    user = mc.get_user_by_token(token)
    return user