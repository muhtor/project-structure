from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("accounts:create")
ME_USER_URL     = reverse("accounts:me")
TOKEN_CREATE_URL = reverse("tokencreate")
TOKEN_REFRESH_URL = reverse("tokenrefresh")

def create_user(**params):
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            "user": {
                "email": "test@gobazar.com",
                "password": "testpass"
            }
        }
        res = self.client.post(CREATE_USER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['user']['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating user that already exists fails"""
        payload = {"user": {"email": "test@gobazar.com", "password": "testpass"}}
        create_user(**payload["user"])

        # creating user with API using same credentials
        res = self.client.post(CREATE_USER_URL, payload, format="json")
        self.assertIn("errors", res.data)
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 8 characters. This is default 8 character limit by Django."""
        payload = {"user": {"email": "test@gobazar.com", "password": "pw"}}
        res = self.client.post(CREATE_USER_URL, payload, format="json")
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payload['user']['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        payload = {"email": "test@gobazar.com", "password": "testpass"}
        create_user(**payload)
        
        res = self.client.post(TOKEN_CREATE_URL, payload, format="json")
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(email="test@gobazar.com", password="testpass")
        payload = {"email": "test@gobazar.com", "password": "testfail"}
        res = self.client.post(TOKEN_CREATE_URL, payload, format="json")
        self.assertNotIn("access", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_no_user(self):
        """Test that token is not created if user doesn't exist"""
        payload = {"email": "test@gobazar.com", "password": "testpass"}
        res = self.client.post(TOKEN_CREATE_URL, payload, format="json")
        self.assertNotIn("access", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)        

    def test_create_token_missing_fields(self):
        """Test that email and password are required"""
        payload = {"email": "test", "password": ""}
        res = self.client.post(TOKEN_CREATE_URL, payload, format="json")
        self.assertNotIn("access", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)       

class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email="test@gobazar.com",
            password = "testpass"
        )
        self.client = APIClient()
        res = self.client.post(TOKEN_CREATE_URL, {"email": "test@gobazar.com", "password": "testpass"}, format="json")
        self.access_token = res.data["access"]
        self.refresh_token = res.data["refresh"]

    def test_retrieve_profile_success(self):
        """Test profile info for logged in user"""
        self.client.force_authenticate(user=self.user)
        res = self.client.get(ME_USER_URL)
        self.assertIn("email", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=None)
    
    def test_retrieve_profile_logout(self):
        """Test profile cannot be seen if not logged out"""
        res = self.client.get(ME_USER_URL)
        self.assertNotIn("email", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)        
    
    def test_inactive_user_api_simplejwt(self):
        """Test that inactive user is not able to get an access token"""
        self.user.is_active = False
        self.user.save()
        res = self.client.post(TOKEN_CREATE_URL, {"email": "test@gobazar.com", "password": "testpass"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_profile_fail_using_jwt(self):
        """Test profile info using incorrect jwt token"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + "abc")
        res = self.client.get(ME_USER_URL)
        self.assertNotIn("email", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_profile_success_using_jwt(self):
        """Test profile info using correct jwt token"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)
        res = self.client.get(ME_USER_URL)
        self.assertIn("email", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK) 

    def test_create_token_using_refresh_token_fail(self):
        """Test that creating access token using incorrect refresh token fails"""
        res = self.client.post(TOKEN_REFRESH_URL, {"token": self.refresh_token}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        res = self.client.post(TOKEN_REFRESH_URL, {"refresh": "abc"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_using_refresh_token_success(self):
        """Test that creating access token using correct refresh token succeeds"""
        res = self.client.post(TOKEN_REFRESH_URL, {"refresh": self.refresh_token}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # quick test new access token works
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + res.data["access"])
        res = self.client.get(ME_USER_URL)
        self.assertIn("email", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)              


     