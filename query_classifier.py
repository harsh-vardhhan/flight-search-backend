from difflib import SequenceMatcher

def get_fuzzy_matches(word: str, keywords: set, threshold: float = 0.75) -> bool:
    """
    Check if a word fuzzy matches any keyword in the set
    Uses difflib.SequenceMatcher for similarity scoring
    
    Args:
        word: The word to check
        keywords: Set of keywords to match against
        threshold: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        bool: True if word matches any keyword above threshold
    """
    for keyword in keywords:
        similarity = SequenceMatcher(None, word.lower(), keyword.lower()).ratio()
        if similarity >= threshold:
            return True
    return False

def is_flight_related_query(query: str) -> bool:
    """
    Enhanced check for flight-related queries using fuzzy matching for typo tolerance
    """
    # Core flight-related keywords
    flight_keywords = {
        'flight', 'flights', 'fly', 'flying',
        'air', 'airline', 'airlines', 'airport', 'airports', 'airways',
        'travel', 'travels', 'trip', 'trips', 'journey', 'journeys',
        'destination', 'destinations', 'dest',
        'origin', 'origins', 'route', 'routes', 'path', 'paths', 'connection', 'connections',
        'price', 'prices', 'fare', 'fares', 'cost', 'costs', 'expensive', 'cheap', 'cheaper', 'cheapest',
        'direct', 'nonstop', 'non-stop', 'connecting', 'connect',
        'departure', 'depart', 'departing', 'arrive', 'arrives', 'arriving', 'arrival',
        'domestic', 'international', 'book', 'booking', 'reserve', 'reservation',
        'ticket', 'tickets', 'seat', 'seats', 'class', 'economy', 'business', 'first'
    }

    # Location indicators that strongly suggest a flight query
    location_indicators = {'from', 'to', 'between', 'via', 'through'}

    # Time-related keywords that in context suggest flights
    time_keywords = {'today', 'tomorrow', 'next', 'week', 'month', 'morning', 'evening', 'night'}

    # Clean and tokenize the query
    query = query.lower().strip()
    query_words = query.split()

    # Check each word in the query
    for word in query_words:
        # Remove punctuation from word
        clean_word = ''.join(char for char in word if char.isalnum())
        
        # Exact match for location indicators (these are short and shouldn't be fuzzy matched)
        if clean_word in location_indicators:
            return True

        # Fuzzy match for flight keywords
        if get_fuzzy_matches(clean_word, flight_keywords):
            return True

    # Check for price indicators
    if any(char in query for char in ['₹', '$', '€', '£', '¥']):
        # If price symbols are present, check if it's likely about flights
        # by looking for location or travel context
        for word in query_words:
            clean_word = ''.join(char for char in word if char.isalnum())
            if (clean_word in location_indicators or 
                get_fuzzy_matches(clean_word, flight_keywords | time_keywords, threshold=0.8)):
                return True

    # Check for common flight query patterns
    # Pattern: "city1 to city2" or "from city1 to city2"
    if 'to' in query_words:
        to_index = query_words.index('to')
        # Check if there are words before and after 'to' (potential city names)
        if to_index > 0 and to_index < len(query_words) - 1:
            return True

    return False