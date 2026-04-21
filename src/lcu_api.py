class LCUAPI:
    async def __api_request(self, connection, method, url, data=None):
        """Perform REST api request to LCU."""
        res = await connection.request(method, url, data=data)

        if res.status != 200 and res.status != 201:
            print(f"[{method.upper()}] {url} failed: {res.status}")
            return None

        try:
            return await res.json()
        except Exception:
            print(f"[{method.upper()}] {url} returned non-JSON response.")
            return None
        
    async def get(self, connection, url):
        """Wrapper for GET request."""
        return await self.__api_request(connection, 'GET', url)

    async def post(self, connection, url, data=None):
        """Wrapper for POST request."""
        return await self.__api_request(connection, 'POST', url, data=data)
    
    async def put(self, connection, url, data=None):
        """Wrapper for PUT request."""
        return await self.__api_request(connection, 'PUT', url, data=data)

    async def get_bot_summoner(self, connection):
        """Get bot information."""
        return await self.get(connection, '/lol-summoner/v1/current-summoner')

    async def get_player_by_puuid(self, connection, puuid):
        """Get a player information by puuid."""
        return await self.get(connection, f'/lol-summoner/v2/summoners/puuid/{puuid}')

    async def send_message_by_puuid(self, connection, puuid, message):
        """Send a message to a player by their puuid."""
        return await self.post(
            connection,
            f'/lol-chat/v1/conversations/{puuid}/messages',
            data={'body': message}
        )
    
    async def accept_friend_request(self, connection, puuid):
        """Accept friend request from a player by puuid."""
        return await self.put(
            connection,
            f'/lol-chat/v2/friend-requests/{puuid}',
            data={'direction': "in"}
        )
