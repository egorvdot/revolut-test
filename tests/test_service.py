import unittest

from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth

from service import app

client = TestClient(app)
credentials = HTTPBasicAuth('codelock', 'iloveyou')


class TestTransformationService(unittest.TestCase):

    def test_transformation_unauthorized(self):
        response = client.put(url='/transformation')
        self.assertEqual(response.status_code, 401)

    def test_transformation_bad_request(self):
        response = client.put(
            url='/transformation',
            json={},
            auth=credentials,
        )
        self.assertEqual(response.status_code, 422)

    def test_transformation_task_example(self):
        response = client.put(
            url='/transformation',
            json={
                'nesting_levels': ['currency', 'country', 'city'],
                'flat_dicts': [
                    {'country': 'US', 'city': 'Boston', 'currency': 'USD', 'amount': 100},
                    {'country': 'FR', 'city': 'Paris', 'currency': 'EUR', 'amount': 20},
                    {'country': 'FR', 'city': 'Lyon', 'currency': 'EUR', 'amount': 11.4},
                    {'country': 'ES', 'city': 'Madrid', 'currency': 'EUR', 'amount': 8.9},
                    {'country': 'UK', 'city': 'London', 'currency': 'GBP', 'amount': 12.2},
                    {'country': 'UK', 'city': 'London', 'currency': 'FBP', 'amount': 10.9},
                ],
            },
            auth=credentials,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'USD': {
                    'US': {'Boston': [{'amount': 100}]},
                },
                'EUR': {
                    'FR': {'Paris': [{'amount': 20}], 'Lyon': [{'amount': 11.4}]},
                    'ES': {'Madrid': [{'amount': 8.9}]},
                },
                'GBP': {
                    'UK': {'London': [{'amount': 12.2}]},
                },
                'FBP': {
                    'UK': {'London': [{'amount': 10.9}]},
                },
            },
        )

    def test_transformation_unexpected_nesting_level(self):
        response = client.put(
            url='/transformation',
            json={
                'nesting_levels': ['a', 'B'],
                'flat_dicts': [{'a': 1, 'b': 2}],
            },
            auth=credentials,
        )
        self.assertEqual(response.status_code, 400)

    def test_transformation_(self):
        response = client.put(
            url='/transformation',
            json={
                'nesting_levels': ['a', 'B'],
                'flat_dicts': [{'a': 1, 'b': 2}],
            },
            auth=credentials,
        )
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
