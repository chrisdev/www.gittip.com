from __future__ import print_function, unicode_literals

from Cookie import SimpleCookie

from aspen.utils import utcnow
import gittip
from gittip.security.user import User, SESSION, SESSION_REFRESH
from gittip.testing import Harness


class TestUser(Harness):

    def test_anonymous_user_is_anonymous(self):
        user = User()
        assert user.ANON

    def test_anonymous_user_is_not_admin(self):
        user = User()
        assert not user.ADMIN

    def test_known_user_is_known(self):
        self.make_participant('alice')
        alice = User.from_username('alice')
        assert not alice.ANON

    def test_username_is_case_insensitive(self):
        self.make_participant('AlIcE')
        actual = User.from_username('aLiCe').participant.username_lower
        assert actual == 'alice'

    def test_known_user_is_not_admin(self):
        self.make_participant('alice')
        alice = User.from_username('alice')
        assert not alice.ADMIN

    def test_admin_user_is_admin(self):
        self.make_participant('alice', is_admin=True)
        alice = User.from_username('alice')
        assert alice.ADMIN


    # ANON

    def test_unreviewed_user_is_not_ANON(self):
        self.make_participant('alice', is_suspicious=None)
        alice = User.from_username('alice')
        assert alice.ANON is False

    def test_whitelisted_user_is_not_ANON(self):
        self.make_participant('alice', is_suspicious=False)
        alice = User.from_username('alice')
        assert alice.ANON is False

    def test_blacklisted_user_is_ANON(self):
        self.make_participant('alice', is_suspicious=True)
        alice = User.from_username('alice')
        assert alice.ANON is True


    # session token

    def test_user_from_bad_session_token_is_anonymous(self):
        user = User.from_session_token('deadbeef')
        assert user.ANON

    def test_user_from_expired_session_is_anonymous(self):
        self.make_participant('alice')
        user = User.from_username('alice')
        user.sign_in(SimpleCookie())
        token = user.participant.session_token
        user.participant.set_session_expires(utcnow())
        user = User.from_session_token(token)
        assert user.ANON

    def test_user_from_None_session_token_is_anonymous(self):
        self.make_participant('alice')
        self.make_participant('bob')
        user = User.from_session_token(None)
        assert user.ANON

    def test_user_can_be_loaded_from_session_token(self):
        self.make_participant('alice')
        user = User.from_username('alice')
        user.sign_in(SimpleCookie())
        token = user.participant.session_token
        actual = User.from_session_token(token).participant.username
        assert actual == 'alice'

    def test_session_cookie_is_secure_if_it_should_be(self):
        canonical_scheme = gittip.canonical_scheme
        gittip.canonical_scheme = 'https'
        try:
            cookies = SimpleCookie()
            self.make_participant('alice')
            user = User.from_username('alice')
            user.sign_in(cookies)
            assert '; secure' in cookies[SESSION].output()
        finally:
            gittip.canonical_scheme = canonical_scheme

    def test_session_is_regularly_refreshed(self):
        self.make_participant('alice')
        user = User.from_username('alice')
        user.sign_in(SimpleCookie())
        cookies = SimpleCookie()
        user.keep_signed_in(cookies)
        assert SESSION not in cookies
        cookies = SimpleCookie()
        expires = user.participant.session_expires
        user.participant.set_session_expires(expires - SESSION_REFRESH)
        user.keep_signed_in(cookies)
        assert SESSION in cookies



    # key token

    def test_user_from_bad_api_key_is_anonymous(self):
        user = User.from_api_key('deadbeef')
        assert user.ANON

    def test_user_from_None_api_key_is_anonymous(self):
        self.make_participant('alice')
        self.make_participant('bob')
        user = User.from_api_key(None)
        assert user.ANON

    def test_user_can_be_loaded_from_api_key(self):
        alice = self.make_participant('alice')
        api_key = alice.recreate_api_key()
        actual = User.from_api_key(api_key).participant.username
        assert actual == 'alice'


    def test_user_from_bad_id_is_anonymous(self):
        user = User.from_username('deadbeef')
        assert user.ANON

    def test_suspicious_user_from_username_is_anonymous(self):
        self.make_participant('alice', is_suspicious=True)
        user = User.from_username('alice')
        assert user.ANON

    def test_signed_out_user_is_anonymous(self):
        self.make_participant('alice')
        alice = User.from_username('alice')
        assert not alice.ANON
        alice.sign_out(SimpleCookie())
        assert alice.ANON
