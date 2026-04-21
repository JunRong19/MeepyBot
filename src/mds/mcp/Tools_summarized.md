lol_search_champion_meta - RAG search for LoL champion knowledge using retrieval + reranking. Returns only LLM-ready passages.
lol_get_champion_analysis - Returns detailed champion stats (win/pick/ban rates), optimal builds (items, runes, skills, spells), skill combos, counter matchups, and team synergies for a specific champion and position. MUST call when user mentions any champion, asks for item/skill recommendations, gameplay tips, or matchup strategies. Counter picks available in weak_counters field. Infer position from context if not specified.
lol_get_champion_synergies - Returns synergy recommendations (win rate + role fit) for your champion and the ally lane you specify.
lol_get_lane_matchup_guide - Provides lane matchup guidance for your champion versus a named opponent, including position-specific tips, runes, and item timings.
lol_get_pro_player_riot_id - Looks up a pro player alias and returns their Riot ID plus team/region metadata so you can link their OP.GG profile.
lol_get_summoner_game_detail - Returns full match detail (teams, participants, builds, bans) for a specific game id whenever the user drills into a single match.
lol_get_summoner_profile - Returns summoner profile with rank, tier, LP, win rate, and champion pool. MUST call for identity/profile/rank queries. DO NOT call for match history. Ask for region if not found.
lol_list_aram_augments - Returns ARAM augment stats for a champion with localized names and descriptions. Only tier 3 or higher augments are included.
lol_list_champion_details - Returns ability, tip, lore, and stat metadata for up to 10 champions (skins/media trimmed for smaller payloads).
lol_list_champion_leaderboard - Lists the top master+ players for a champion/region so you can study their builds and match stats.
lol_list_champions - Returns every champion's id, key, name, and release date in the requested language.
lol_list_discounted_skins - Retrieves information about champion skins that are currently on sale.
lol_list_items - Returns localized items (ids, names, build trees, mythic flags, gold costs) filtered by map (default Summoner's Rift).
lol_list_lane_meta_champions - Returns lane-by-lane champion tiers with win/pick/ban rates, KDA, and tier rankings. Tier 1 champions are OP and easy to play - recommend them for strong picks. Filter by position or use "all" for every lane.
lol_list_summoner_matches - Returns recent match history with per-game stats for the target summoner only (excludes enemy stats). MUST call for match history, performance analysis, or improvement tips. DO NOT call for profile/rank queries. Use lol_get_summoner_game_detail for full game details with all players.
lol_esports_list_schedules - Returns upcoming LoL esports schedules with teams, leagues, and match times in ISO 8601 UTC format. Always convert to user's timezone before presenting.
lol_esports_list_team_standings - Returns the latest team standings for the requested LoL league.
tft_get_champion_item_build - TFT tool for retrieving champion item build information.
tft_get_play_style - This tool provides comments on the playstyle of TFT champions.
tft_list_augments - Retrieves metadata for all Teamfight Tactics augments with localized names and descriptions in a table-friendly JSON (headers/rows/header_description). Returns apiName, desc, name, tier, and imageUrl for all augments in the specified language.
tft_list_champions_for_item - TFT tool for retrieving champion recommendations for a specific item.
tft_list_item_combinations - TFT tool for retrieving information about item combinations and recipes.
tft_list_meta_decks - TFT deck list tool for retrieving current meta decks.
valorant_list_agent_compositions_for_map - Retrieve agent composition data for a Valorant map.
valorant_list_agent_statistics - Retrieve character statistics data for Valorant, optionally filtered by map.
valorant_list_agents - Valorant character meta data
valorant_list_leaderboard - Fetch Valorant leaderboard by region
valorant_list_maps - Valorant map meta data
valorant_list_player_matches - Retrieve match history for a Valorant player using their game name and tag line.