class TestHandlers:
    def test_add(self, client):
        """Test the add endpoint"""
        response = client.post("/add", json={"x": 3, "y": 2})
        assert response.status_code == 200
        assert response.json() == {"result": 5}
