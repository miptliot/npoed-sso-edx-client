import logging

from django.conf import settings

from social.utils import handle_http_errors
from social.backends.oauth import BaseOAuth2

log = logging.getLogger(__name__)
# log.info(' '.join(["+" * 40]))


DEFAULT_AUTH_PIPELINE = (
    'third_party_auth.pipeline.parse_query_params',
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'third_party_auth.pipeline.associate_by_email_if_login_api',
    'social.pipeline.user.get_username',
    'third_party_auth.pipeline.set_pipeline_timeout',
    'sso_edx_npoed.pipeline.ensure_user_information',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
    'third_party_auth.pipeline.set_logged_in_cookies',
    'third_party_auth.pipeline.login_analytics',
)

class NpoedBackend(BaseOAuth2):

    name = 'sso_npoed-oauth2'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = '{}/oauth2/authorize'.format(settings.SSO_NPOED_URL)
    ACCESS_TOKEN_URL = '{}/oauth2/access_token'.format(settings.SSO_NPOED_URL)
    USER_DATA_URL = '{url}/oauth2/access_token/{access_token}/'
    DEFAULT_SCOPE = []
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'

    PIPELINE = DEFAULT_AUTH_PIPELINE
    skip_email_verification = True

    def auth_url(self):
        return '{}&auth_entry={}'.format(
            super(NpoedBackend, self).auth_url(),
            self.data.get('auth_entry', 'login')
        )

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        """Completes loging process, must return user instance"""
        self.strategy.session.setdefault('{}_state'.format(self.name),
                                         self.data.get('state'))
        self.strategy.session.setdefault('next', '/dashboard')
        return super(NpoedBackend, self).auth_complete(*args, **kwargs)

    def pipeline(self, pipeline, pipeline_index=0, *args, **kwargs):
        self.strategy.session.setdefault('auth_entry', 'register')
        return super(NpoedBackend, self).pipeline(
            pipeline=self.PIPELINE, pipeline_index=pipeline_index, *args, **kwargs
        )

    def get_user_details(self, response):
        """ Return user details from MIPT account. """
        return response

    def user_data(self, access_token, *args, **kwargs):
        """ Grab user profile information from MIPT. """
        return self.get_json(
            '{}/users/me'.format(settings.SSO_NPOED_URL),
            params={'access_token': access_token},
            headers={'Authorization': 'access_token {}'.format(access_token)},
        )

    def do_auth(self, access_token, *args, **kwargs):
        """Finish the auth process once the access_token was retrieved"""
        data = self.user_data(access_token)
        data['access_token'] = access_token
        kwargs.update(data)
        kwargs.update({'response': data, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)


class NpoedBackendCMS(NpoedBackend):

    name = 'sso_npoed_cms-oauth2'
