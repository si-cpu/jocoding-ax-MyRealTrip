# Search and exclusion rules

## Available official interfaces

### Partner REST client

Run `../../scripts/myrealtrip_api.py` relative to the skill folder.

Commands:

- `airport-autocomplete`
- `flight-bulk-lowest`
- `stay-regions`
- `stay-search`
- `tna-categories`
- `tna-search`
- `tna-detail`
- `tna-options`

The client reads `MYREALTRIP_API_KEY` from the environment and never prints it.

### MyRealTrip MCP

Relevant tools:

- Current time: `getCurrentTime` returns Korea Standard Time
- Flights: `searchDomesticFlights`, `searchInternationalFlights`, `flightsFareCalendar`
- Stays: `searchStays`, `getStayDetail`
- TNA: `getCategoryList`, `searchTnas`, `getTnaDetail`, `getTnaOptions`

The Partner REST bulk-lowest endpoint supplies international calendar-fare discovery. MCP flight search supplies a live follow-up for a route the user selects.

## 공항에서 어디로 갈까

### Airport identity

`POST /v1/products/flight/airport-autocomplete`

- Use `airports[].airport.code`.
- Never use `airports[].city.code`.
- Resolve both the departure and shortlisted destination codes to human-readable airport, city, and country data.

### Destination discovery

`POST /v1/products/flight/calendar/bulk-lowest`

- Input: exact departure `airport.code` and `period` from 3 to 7 days.
- Coverage: international routes only.
- Preserve `fromCity`, `toCity`, `period`, `departureDate`, `returnDate`, `totalPrice`, `airline`, `transfer`, and `averagePrice` when returned.
- `totalPrice` is a calendar lowest fare. It is not proof of live seats or the checkout price.
- Resolve `toCity` through airport autocomplete before showing it. Do not guess a city from an unfamiliar code.
- Exclude user-declared familiar countries and cities after code resolution.

After the user selects a destination, use `searchInternationalFlights` with exact dates and airport codes. Present its returned URL and price as the live follow-up, and keep the calendar fare visibly separate.

Do not replace an unavailable Partner API call with a model-generated destination list, web popularity ranking, or hand-picked routes. Do not represent the international bulk result as domestic coverage.

## 어디서 잘까

### Region

`POST /v1/products/accommodation/region-autocomplete`

- Select exact `CITY` only.
- Use `regionId`.
- Reject station, airport, attraction, and non-exact region names.

### Search

`POST /v1/products/accommodation/search`

- Page starts at 0; size is 1–50.
- Preserve `itemId`, prices, rating, and `productUrl`.
- The response does not expose accommodation type.

Use MCP `searchStays` for type verification. Common values include `HOTELS`, `BNB_V2`, `HOSTELS`, `TRADITIONAL_ACCOMMODATION`, `MOTELS`, `RESORTS`, and `PENSION_PRIVATEHOUSE`.

Use structured description, not name, to distinguish hotel, hostel, ryokan, guesthouse, or apartment. Cross-check MCP `gid` with REST `itemId` when possible.

## 오늘·내일 뭐 하지

### Search

`POST /v1/products/tna/categories`

- Category values differ by city; never hardcode them globally.

`POST /v1/products/tna/search`

- Page starts at 1; size is 1–100.
- Preserve `gid`, name, description, category, starting price, rating, and `productUrl`.
- Description commonly follows `도시 ∙ 카테고리`.
- Reject missing/mismatched city evidence and explicit title conflicts.

`POST /v1/products/tna/detail`

- Use `gid` from search.
- Explain only returned descriptions, inclusions/exclusions, itineraries, and reviews.

### Date availability

`POST /v1/products/tna/options`

- Required: `gid`, `selectedDate` in `YYYY-MM-DD`.
- Treat `options: []` as not bookable for that date.
- Use returned option price rather than search starting price when claiming date-specific availability.
- Preserve minimum and available purchase quantities when returned.

MCP `getTnaOptions` is the fallback. If it returns an automatic-lookup restriction, relay that message and do not label the product bookable.

### Familiarity overlap

Assign `OVERLAP` only when returned data proves a direct relation:

1. Hobby or unambiguous synonym appears in title, category, or description.
2. Central activity is a direct instance of the hobby.
3. Product exists primarily to watch, visit, learn, or participate in the hobby.

Keep `UNCLEAR` candidates. Uncertainty is not evidence of overlap.

Never infer personality, treat culture as the opposite of sports, expand one hobby into a lifestyle, or use popularity/price/rating as overlap evidence.
