import urllib.parse
from typing import Any, Optional, List, Generator

from pydantic import BaseModel, Extra

from coles_vs_woolies.search import types
from coles_vs_woolies.search.session import new_session


def _woolies_session():
    session = new_session()
    session.get(url='https://www.woolworths.com.au')
    return session


_session = _woolies_session()


class Product(types.Product, BaseModel, extra=Extra.allow):
    merchant = 'woolies'

    TileID: int  # 1
    Stockcode: int  # 153266
    Barcode: Optional[str]  # "9300617296027"
    GtinFormat: int  # 13
    CupPrice: Optional[float]  # 1.67
    InstoreCupPrice: Optional[float]  # 1.67
    CupMeasure: str  # "100G"
    CupString: str  # "$1.67 / 100G"
    InstoreCupString: str  # "$1.67 / 100G"
    HasCupPrice: bool  # true
    InstoreHasCupPrice: bool  # true
    Price: Optional[float]  # None if `IsAvailable=False`
    InstorePrice: Optional[float]  # 6 if `IsAvailable=False`
    Name: str  # "Cadbury Dairy Milk Chocolate Block"
    DisplayName: str  # "Cadbury Dairy Milk Chocolate Block 360g"
    UrlFriendlyName: str  # "cadbury-dairy-milk-chocolate-block"
    Description: str  # " Cadbury Dairy Milk Chocolate<br>Block  360G"
    SmallImageFile: str  # "https://cdn0.woolworths.media/content/wowproductimages/small/153266.jpg"
    MediumImageFile: str  # "https://cdn0.woolworths.media/content/wowproductimages/medium/153266.jpg"
    LargeImageFile: str  # "https://cdn0.woolworths.media/content/wowproductimages/large/153266.jpg"
    IsNew: bool  # false
    IsHalfPrice: bool  # false
    IsOnlineOnly: bool  # false
    IsOnSpecial: bool  # false
    InstoreIsOnSpecial: bool  # false
    IsEdrSpecial: bool  # false
    SavingsAmount: Optional[float]  # 0
    InstoreSavingsAmount: Optional[float]  # 0
    WasPrice: float  # 6
    InstoreWasPrice: float  # 6
    QuantityInTrolley: int  # 0
    Unit: str  # "Each"
    MinimumQuantity: int  # 1
    HasBeenBoughtBefore: bool  # false
    IsInTrolley: bool  # false
    Source: str  # "SearchServiceSearchProducts"
    SupplyLimit: int  # 36
    ProductLimit: int  # 36
    MaxSupplyLimitMessage: str  # "36 item limit"
    IsRanged: bool  # true
    IsInStock: bool  # true
    PackageSize: str  # "360G"
    IsPmDelivery: bool  # false
    IsForCollection: bool  # true
    IsForDelivery: bool  # true
    IsForExpress: bool  # true
    ProductRestrictionMessage: Optional[str]  # null
    ProductWarningMessage: Optional[str]  # null
    UnitWeightInGrams: int  # 0
    SupplyLimitMessage: str  # "'Cadbury Dairy Milk Chocolate Block' has a supply limit of 36. [...]'"
    SmallFormatDescription: str  # "Cadbury Dairy Milk Chocolate Block "
    FullDescription: str  # "Cadbury Dairy Milk Chocolate Block "
    IsAvailable: bool  # true
    InstoreIsAvailable: bool  # false
    IsPurchasable: bool  # true
    InstoreIsPurchasable: bool  # false
    AgeRestricted: bool  # false
    DisplayQuantity: int  # 1
    RichDescription: Optional[str]  # null
    IsDeliveryPass: bool  # false
    HideWasSavedPrice: bool  # false
    Brand: Optional[str]  # "Cadbury"
    IsRestrictedByDeliveryMethod: bool  # false
    Diagnostics: str  # "0"
    IsBundle: bool  # false
    IsInFamily: bool  # false
    ChildProducts: Any  # null
    UrlOverride: Optional[str]  # null

    def __str__(self):
        price_str = f"unavailable (was ${self.InstoreWasPrice})"
        if self.IsAvailable:
            price_str = f'${self.Price}'
            if self.IsOnSpecial:
                price_str += f' (save ${self.WasPrice - self.Price})'
        return f"{self.DisplayName} | {price_str}"

    @property
    def display_name(self) -> str:
        return self.DisplayName

    @property
    def price(self) -> Optional[float]:
        return self.Price if self.IsAvailable else None

    @property
    def is_on_special(self) -> Optional[bool]:
        return self.IsOnSpecial

    @property
    def link(self) -> str:
        return f'https://www.woolworths.com.au/shop/productdetails/{self.Stockcode}/{self.UrlFriendlyName}'

    @classmethod
    def fetch_product(cls, product_id: str):
        url = f'https://www.woolworths.com.au/apis/ui/product/detail/{product_id}?isMobile=false'
        response = _session.get(url=url)
        return Product.parse_obj(response.json())


class ProductSearchResult(BaseModel, extra=Extra.allow):
    Products: Optional[List[Product]]
    Name: str
    DisplayName: str


class ProductPageSearchResult(BaseModel, extra=Extra.allow):
    Products: Optional[List[ProductSearchResult]]
    SearchResultsCount: int
    Corrections: Optional[Any]
    SuggestedTerm: Optional[Any]


def im_feeling_lucky(search_term: str) -> Generator[Product, None, None]:
    paginated_search = search(search_term)
    for page in paginated_search:
        for product in page.Products:
            for _product in product.Products:
                yield _product


def search(search_term: str, page=1) -> Generator[ProductPageSearchResult, None, None]:
    url = 'https://www.woolworths.com.au/apis/ui/Search/products'
    body = {
        'Filters': [],
        'IsSpecial': False,
        'Location': f'/shop/search/products?{urllib.parse.urlencode({"searchTerm": search_term})}',
        'PageNumber': page,
        'PageSize': 36,
        'SearchTerm': search_term,
        'SortType': "TraderRelevance"
    }
    while True:
        response = _session.post(
            url=url,
            # cookies={'bm_sz': _session.cookies.get('bm_sz')},
            json=body,
        ).json()
        search_page = ProductPageSearchResult.parse_obj(response)
        if search_page.Products is None:
            break
        yield search_page
        body['PageNumber'] += 1

def ingredientsToProductsWoW(items):
    url = 'https://graph.whisk.com/v1/carts'
    body = {
        "combineItems": 'true',
        "items": items,
        "language":"en-GB",
        "retailerId":"woolworths",
    }
    header = {
    'authority': 'graph.whisk.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Token OvupLC3bOkkbbEzqatZA526kWNijke90UZ3opCHvOf9gTkgqBxmIxb61ecEPBIVh',
    'content-type': 'application/json',
    'dnt': '1',
    'origin': 'https://www.woolworths.com.au',
    'referer': 'https://www.woolworths.com.au/',
    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': "Android",
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36',
    'whisksitedomain': 'woolworths.com.au',
    'whiskwidgetrecipesite': 'woolworths.com.au',
    }

    response = _session.post(
            url=url,
            headers=header,
            # cookies={'bm_sz': _session.cookies.get('bm_sz')},
            json=body,
        ).json()

    return response

# def specialSearch(search_term: str, page=1) -> Generator[ProductPageSearchResult, None, None]:
#     url = 'https://www.woolworths.com.au/apis/ui/Search/products'
#     body = {
#   "categoryId": "specialsgroup.3676",
#   "pageNumber": 1,
#   "pageSize": 36,
#   "sortType": "PriceDesc",
#   "url": "/shop/browse/specials/half-price",
#   "location": "/shop/browse/specials/half-price",
#   "formatObject": "{\"name\":\"Half Price\"}",
#   "isSpecial": 'true',
#   "isBundle": 'false',
#   "isMobile": 'false',
#   "filters": [],
#   "token": "",
#   "enableGp": 'false'
#     }

#     while True:
#         response = _session.post(
#             url=url,
#             # cookies={'bm_sz': _session.cookies.get('bm_sz')},
#             json=body,
#         ).json()
#         search_page = ProductPageSearchResult.parse_obj(response)
#         if search_page.Products is None:
#             break
#         yield search_page
#         body['PageNumber'] += 1



if __name__ == '__main__':
    gen = specialSearch('Cadbury Dairy Milk Chocolate Block 180g')
    print(next(gen))

#WOOLIES APIS
#Login:
#https://www.woolworths.com.au/shop/securelogin


#Add to Cart:
#https://www.woolworths.com.au/api/v3/ui/trolley/update
#HEADERS:
# curl 'https://www.woolworths.com.au/api/v3/ui/trolley/update' \
#   -H 'authority: www.woolworths.com.au' \
#   -H 'accept: application/json, text/plain, */*' \
#   -H 'accept-language: en-US,en;q=0.9' \
#   -H 'content-type: application/json' \
#   -H 'cookie: rxVisitor=16797001744634FDBN7J6UEQE5ITI4SROBNQ1AIMQERAV; at_check=true; ai_user=sp6UCrgH+zgHkt+3tMxh3m|2023-03-24T23:22:55.142Z; AMCVS_4353388057AC8D357F000101%40AdobeOrg=1; fullstoryEnabled=true; s_cc=true; IR_gbd=woolworths.com.au; INGRESSCOOKIE=1679700184.173.454.484681|37206e05370eb151ee9f1b6a1c80a538; dtCookie=v_4_srv_5_sn_91NQ2QGA3D301GBNF4RGBGB3PSN82LU3_app-3Af908d76079915f06_1_ol_0_perc_100000_mul_1_rcs-3Acss_0; mdLogger=false; kampyle_userid=6116-832b-02be-3aa1-a161-4ba8-9d57-2de6; bm_sz=98E908FD60B77B8AAC21422E0C99ADD8~YAAQKwUgF5QpeBaHAQAATs0YIRPv1mSM/iRlVBZ8VXGWAvt4qC6ZzEWU2ubz7aLysmCPFj+pwRxvbeQYLgEsgHNuZLX02dcU13AWeu8n2YSvuePJM5VU01gyYv7yI/D1Uf/TcjueMe/INcbfFZexK2VjinDWg1hidcSCT1ZDawUixNFMTzvly6SGbzjRpOeH0Ori7RT+tKpn/llZ3M5Z8WqTwMR4ukuQJWU0e79OmuEazQoEUZy44SXpAQ7k8mYCJNCtptwqgeqbtDCOqzPZowMuF8r2hs0HSvPYLYR5OppxpDwGqZVhJLPiqOGDUkMda8NHFjlznUiyx9Ruq32aZymS~3753273~3425347; bff_region=syd1; akaalb_woolworths.com.au=~op=www_woolworths_com_au_BFF_SYD1:WOW-BFF-SYD|www_woolworths_com_au_ZoneC:PROD-ZoneC|www_woolworths_com_au_BFF_SYD_Launch:WOW-BFF-SYD|www_woolworths_com_au_BFF_SYD2:WOW-BFF-SYD2|www_woolworths_com_au_ZoneA:PROD-ZoneA|~rv=71~m=PROD-ZoneC:0|WOW-BFF-SYD2:0|PROD-ZoneA:0|~os=43eb3391333cc20efbd7f812851447e6~id=209a01ceb505eedf5ad837070b443e7d; IR_PI=61df1324-cc51-11ed-9226-f58b463ff051%7C1679974945671; AKA_A2=A; BVBRANDID=ab9a1db7-b119-40b4-afe6-ac66da623841; BVImplmain_site=10149; dtSa=-; _uetsid=659ccb90cc5011ed88710dec060b43f7; _uetvid=d1e121f0ca9a11edb23c6b16ec8d4cf4; mbox=session#2a998709574741338ac05085355b837b#1679896464; IR_7464=1679894603545%7C0%7C1679894603545%7C%7C; kampyleUserSession=1679894607083; kampyleUserSessionsCount=6; kampyleSessionPageCounter=1; dtLatC=1; utag_main=v_id:018715eeba3d0012bc5dc078738c0506f001e067019b8$_sn:5$_se:34$_ss:0$_st:1679896531567$vapi_domain:woolworths.com.au$dc_visit:5$ses_id:1679892980822%3Bexp-session$_pn:3%3Bexp-session$dc_event:11%3Bexp-session; AMCV_4353388057AC8D357F000101%40AdobeOrg=179643557%7CMCIDTS%7C19444%7CMCMID%7C40467679595263432621368739985893322168%7CMCOPTOUT-1679901931s%7CNONE%7CvVersion%7C5.5.0; w-rctx=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE2Nzk4OTQ4NjYsImV4cCI6MTY3OTg5ODQ2NiwiaWF0IjoxNjc5ODk0ODY2LCJpc3MiOiJXb29sd29ydGhzIiwiYXVkIjoid3d3Lndvb2x3b3J0aHMuY29tLmF1Iiwic2lkIjoiMCIsInVpZCI6IjE5NmRjM2Q4LTIzZTQtNGY0Mi1iYzg2LTVhNGJhMDdmYWVhYSIsIm1haWQiOiIwIiwiYXV0IjoiU2hvcHBlciIsImF1YiI6IjAiLCJhdWJhIjoiMCIsIm1mYSI6IjEifQ.U7okj_VZNcuufG-ruXyoiVY5d2yT-ASyA1G8IllWLvvNxh1hHhaPMTF_gcGlt9aE8147kHeJCnqEme0HoM7wvhMKiY-ur6qIiKYrTOyZGGFOfqNN_fOCEeVf63LZ_skm9gw5F-RJxOkI8CpO1unxGjZA_Ey6bHNJ7gZS2O7qBkTEM1SwpduKhYhOFbKpVssqBH8_xz8oOFynvDR4zTShW2772hGFyeywl6-wKnZhesuQUqulW3e7_LMqchjpYL-pBy9cQXvRJZQDr52cep0pFDMhJmIW7dGjUXBuE_JM7oeKZEWcJdWgbPBrMg-Xxs6ZpDPccE-17109h1XppSANqQ; wow-auth-token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE2Nzk4OTQ4NjYsImV4cCI6MTY3OTg5ODQ2NiwiaWF0IjoxNjc5ODk0ODY2LCJpc3MiOiJXb29sd29ydGhzIiwiYXVkIjoid3d3Lndvb2x3b3J0aHMuY29tLmF1Iiwic2lkIjoiMCIsInVpZCI6IjE5NmRjM2Q4LTIzZTQtNGY0Mi1iYzg2LTVhNGJhMDdmYWVhYSIsIm1haWQiOiIwIiwiYXV0IjoiU2hvcHBlciIsImF1YiI6IjAiLCJhdWJhIjoiMCIsIm1mYSI6IjEifQ.U7okj_VZNcuufG-ruXyoiVY5d2yT-ASyA1G8IllWLvvNxh1hHhaPMTF_gcGlt9aE8147kHeJCnqEme0HoM7wvhMKiY-ur6qIiKYrTOyZGGFOfqNN_fOCEeVf63LZ_skm9gw5F-RJxOkI8CpO1unxGjZA_Ey6bHNJ7gZS2O7qBkTEM1SwpduKhYhOFbKpVssqBH8_xz8oOFynvDR4zTShW2772hGFyeywl6-wKnZhesuQUqulW3e7_LMqchjpYL-pBy9cQXvRJZQDr52cep0pFDMhJmIW7dGjUXBuE_JM7oeKZEWcJdWgbPBrMg-Xxs6ZpDPccE-17109h1XppSANqQ; prodwow-auth-token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE2Nzk4OTQ4NjYsImV4cCI6MTY3OTg5ODQ2NiwiaWF0IjoxNjc5ODk0ODY2LCJpc3MiOiJXb29sd29ydGhzIiwiYXVkIjoid3d3Lndvb2x3b3J0aHMuY29tLmF1Iiwic2lkIjoiMCIsInVpZCI6IjE5NmRjM2Q4LTIzZTQtNGY0Mi1iYzg2LTVhNGJhMDdmYWVhYSIsIm1haWQiOiIwIiwiYXV0IjoiU2hvcHBlciIsImF1YiI6IjAiLCJhdWJhIjoiMCIsIm1mYSI6IjEifQ.U7okj_VZNcuufG-ruXyoiVY5d2yT-ASyA1G8IllWLvvNxh1hHhaPMTF_gcGlt9aE8147kHeJCnqEme0HoM7wvhMKiY-ur6qIiKYrTOyZGGFOfqNN_fOCEeVf63LZ_skm9gw5F-RJxOkI8CpO1unxGjZA_Ey6bHNJ7gZS2O7qBkTEM1SwpduKhYhOFbKpVssqBH8_xz8oOFynvDR4zTShW2772hGFyeywl6-wKnZhesuQUqulW3e7_LMqchjpYL-pBy9cQXvRJZQDr52cep0pFDMhJmIW7dGjUXBuE_JM7oeKZEWcJdWgbPBrMg-Xxs6ZpDPccE-17109h1XppSANqQ; _abck=E5C19F16769014A645CFB885D24514B1~0~YAAQpAUgFyPcVhCHAQAAR2qJIQn/7KX8ar0Bz+8Muee/KlSDMHUHkR/lgy8w3nc+a6dIbhqynjKJzIkyEVHboCiVou27HN5LLoS5uMB/je0/7m2odMBchWnbA10sL2iuc+BtttnBs8JrjNZqU4zo4A+Q1O938P4pC7zXJdVn2rvcjagmfxcFv2L1FN1t6jbz5+q36al08bvCkatwjzYYhwqOIbFr2qWeL+dvRquU8TV+Ntoii+Mz3jtPZnLpWa63r6soZcAIGKSqn5fZsL43Gszsef0orcdKegkrCaGDZTKnG05xpbkgnWmUlCiGBtptHhaPBuesxCfGF88SwlWW0pZ6GyxyScXFZI3B4efXbeAknUsLXVc7aH9ONPjBtbW/kr97HKFA~-1~-1~-1; bm_sv=523F6B6B18AEF6ABCDD6EB0955167221~YAAQpAUgFyTcVhCHAQAASGqJIRMbDrC8CrvDUqLumd1G03wBu4udEvPVXmRqDBN4QEgqtOxcvs4qs7SiEP0ALNq58UOan4AC953J4ZlrQGed510HR2+owEvrwssfjfkfHiUNgzXCQxVt5VZFDJTb7j1jk45pb9gWexhOcOSvPrHtLaa2Gh5Cit8HC9cuIXx/HLO7JzKOVSUME1tDxvPHfG0v5iQTgvNBpq8G1cNlDvk0zJFYH8k5zlCd17bP6QLmGnZTwVz2qVM=~1; ai_session=Bn/dEaZlJ0NCb7BipZC7qs|1679893070192|1679894869975; rxvt=1679897174719|1679892082468; dtPC=5$494602172_432h310vPHFGBUPRKGAJOIUHPVEGBDSNIBBSRFQM-0e0' \
#   -H 'dnt: 1' \
#   -H 'origin: https://www.woolworths.com.au' \
#   -H 'referer: https://www.woolworths.com.au/shop/recipes/aussie-beef-sausages-with-onion-relish' \
#   -H 'request-context: appId=cid-v1:099a45be-5030-453c-b870-6f6cb4dacdb8' \
#   -H 'request-id: |371f6ef8cb494a6d896e6222cb4ea5ab.5dacea4c5c014236' \
#   -H 'sec-ch-ua: "Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"' \
#   -H 'sec-ch-ua-mobile: ?1' \
#   -H 'sec-ch-ua-platform: "Android"' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'traceparent: 00-371f6ef8cb494a6d896e6222cb4ea5ab-5dacea4c5c014236-01' \
#   -H 'user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36' \
#BODY:
#   --data-raw '{"items":[{"stockcode":253320,"diagnostics":"0","quantity":1,"source":"foodhub-recipe","searchTerm":null},{"stockcode":135306,"diagnostics":"8","quantity":1,"source":"foodhub-recipe","searchTerm":null},{"stockcode":136510,"diagnostics":"9","quantity":1,"source":"foodhub-recipe","searchTerm":null},{"stockcode":138082,"diagnostics":"7","quantity":1,"source":"foodhub-recipe","searchTerm":null},{"stockcode":144497,"diagnostics":"10","quantity":2,"source":"foodhub-recipe","searchTerm":null},{"stockcode":256880,"diagnostics":"2","quantity":1,"source":"foodhub-recipe","searchTerm":null},{"stockcode":54900,"diagnostics":"4","quantity":1,"source":"foodhub-recipe","searchTerm":null},{"stockcode":720342,"diagnostics":"6","quantity":1,"source":"foodhub-recipe","searchTerm":null},{"stockcode":820196,"diagnostics":"1","quantity":1,"source":"foodhub-recipe","searchTerm":null}]}' \
#   --compressed
