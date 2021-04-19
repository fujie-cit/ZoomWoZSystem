import requests
import json


class TMDB:
    def __init__(self, token):
        self.token = token
        self.headers_ = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json;charset=utf-8'}
        self.base_url_ = 'https://api.themoviedb.org/3/'
        self.img_base_url_ = 'https://image.tmdb.org/t/p/w500'

    def _json_by_get_request(self, url, params={}):
        res = requests.get(url, headers=self.headers_, params=params)
        return json.loads(res.text)

    def discover_movies(self, params):
        """
        ジャンル, 公開日, 人気などから映画の検索

        params: dict
          'with_genres': ジャンルID (str) ex. '28'(アクション)
          'region': 国 (str)  ex. 'JP'
          'language': 言語 (str) ex. 'ja-JP'
          'sort_by': 並び替え方法 (str) ex. 'release_date.desc'
          'release_date.lte': この日までに公開したものを表示 ex. '2021-03-17'

        その他細かい指定が可能
        参照: https://developers.themoviedb.org/3/discover/movie-discover
        """
        url = f'{self.base_url_}discover/movie'
        return self._json_by_get_request(url, params)

    def search_movies(self, query, language='ja-JP'):
        params = {'query': query, 'language': language}
        url = f'{self.base_url_}search/movie'
        return self._json_by_get_request(url, params)

    def search_persons(self, query, language='ja-JP'):
        params = {'query': query, 'language': language}
        url = f'{self.base_url_}search/person'
        return self._json_by_get_request(url, params)

    def get_movie(self, movie_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}movie/{movie_id}'
        return self._json_by_get_request(url, params)

    def get_movie_account_states(self, movie_id):
        url = f'{self.base_url_}movie/{movie_id}/account_states'
        return self._json_by_get_request(url)

    def get_movie_alternative_titles(self, movie_id, country=None):
        url = f'{self.base_url_}movie/{movie_id}/alternative_titles'
        return self._json_by_get_request(url)

    def get_movie_changes(self, movie_id, start_date=None, end_date=None):
        url = f'{self.base_url_}movie/{movie_id}'
        return self._json_by_get_request(url)

    def get_movie_credits(self, movie_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}movie/{movie_id}/credits'
        return self._json_by_get_request(url, params)

    def get_movie_external_ids(self, movie_id):
        url = f'{self.base_url_}movie/{movie_id}/external_ids'
        return self._json_by_get_request(url)

    def get_movie_images(self, movie_id, language='ja-JP'):
        url = f'{self.base_url_}movie/{movie_id}/images'
        return self._json_by_get_request(url)

    def get_movie_keywords(self, movie_id):
        url = f'{self.base_url_}movie/{movie_id}/keywords'
        return self._json_by_get_request(url)

    def get_movie_release_dates(self, movie_id):
        url = f'{self.base_url_}movie/{movie_id}/release_dates'
        return self._json_by_get_request(url)

    def get_movie_videos(self, movie_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}movie/{movie_id}/videos'
        return self._json_by_get_request(url, params)

    def get_movie_translations(self, movie_id):
        url = f'{self.base_url_}movie/{movie_id}/translations'
        return self._json_by_get_request(url)

    def get_movie_recommendations(self, movie_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}movie/{movie_id}/recommendations'
        return self._json_by_get_request(url, params)

    def get_similar_movies(self, movie_id, language='ja-JP'):
        params = {'query': query, 'language': language}
        url = f'{self.base_url_}movie/{movie_id}/similar'
        return self._json_by_get_request(url, params)

    def get_movie_reviews(self, movie_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}movie/{movie_id}/reviews'
        return self._json_by_get_request(url, params)

    def get_movie_lists(self, movie_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}movie/{movie_id}/lists'
        return self._json_by_get_request(url, params)

    def get_latest_movies(self, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}movie/latest'
        return self._json_by_get_request(url, params)

    def get_now_playing_movies(self, language='ja-JP', region='JP'):
        params = {'language': language, 'region': region}
        url = f'{self.base_url_}movie/now_playing'
        return self._json_by_get_request(url, params)

    def get_popular_movies(self, language='ja-JP', region='JP'):
        params = {'language': language, 'region': region}
        url = f'{self.base_url_}movie/popular'
        return self._json_by_get_request(url, params)

    def get_top_rated_movies(self, language='ja-JP', region='JP'):
        params = {'language': language, 'region': region}
        url = f'{self.base_url_}movie/top_rated'
        return self._json_by_get_request(url, params)

    def get_upcoming_movies(self, language='ja-JP', region='JP'):
        params = {'language': language, 'region': region}
        url = f'{self.base_url_}movie/upcoming'
        return self._json_by_get_request(url, params)

    def get_person_info(self, person_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}person/{person_id}'
        return self._json_by_get_request(url, params)

    def get_person_credit(self, person_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}person/{person_id}/movie_credits'
        return self._json_by_get_request(url, params)

    def get_credits_info(self, credit_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}credit/{credit_id}'
        return self._json_by_get_request(url, params)

    def get_company_info(self, company_id, language='ja-JP'):
        params = {'language': language}
        url = f'{self.base_url_}company/{company_id}'
        return self._json_by_get_request(url, params)

    def get_genre_list(self, language=None):
        params = {'language': language}
        url = f'{self.base_url_}genre/movie/list'
        return self._json_by_get_request(url, params)
