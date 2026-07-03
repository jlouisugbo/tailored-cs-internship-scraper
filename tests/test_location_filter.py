from location_filter import is_us_location


def test_city_state_abbreviation_is_us():
    assert is_us_location("San Francisco, CA") is True


def test_united_states_literal_is_us():
    assert is_us_location("United States") is True


def test_remote_with_no_country_defaults_to_us():
    assert is_us_location("Remote") is True


def test_blank_location_defaults_to_us():
    assert is_us_location("") is True


def test_london_uk_is_not_us():
    assert is_us_location("London, UK") is False


def test_toronto_ontario_is_not_us():
    assert is_us_location("Toronto, ON") is False


def test_bangalore_india_is_not_us():
    assert is_us_location("Bangalore, India") is False


def test_multi_location_with_one_us_segment_is_us():
    assert is_us_location("San Francisco, CA</br>London, UK") is True


def test_multi_location_all_non_us_is_not_us():
    assert is_us_location("London, UK</br>Toronto, ON") is False


def test_html_wrapped_multi_location_parses_correctly():
    location = (
        "<details><summary>**5 locations**</summary>"
        "San Francisco, CA</br>Palo Alto, CA</br>New York, NY</br>"
        "Seattle, WA</br>Burlington, MA</details>"
    )
    assert is_us_location(location) is True


def test_case_insensitive_country_match():
    assert is_us_location("london, united kingdom") is False


def test_bogota_colombia_is_not_us():
    assert is_us_location("Colombia - Bogota") is False


def test_buenos_aires_argentina_is_not_us():
    assert is_us_location("Argentina - Buenos Aires") is False


def test_country_dash_city_format_is_not_us():
    assert is_us_location("Italy - Milan") is False
    assert is_us_location("United Arab Emirates - Dubai") is False
    assert is_us_location("Finland - Espoo") is False
    assert is_us_location("Denmark - Copenhagen") is False


def test_georgia_the_us_state_is_not_confused_with_the_country():
    assert is_us_location("Atlanta, Georgia") is True


def test_international_location_is_not_us():
    assert is_us_location("International") is False
    assert is_us_location("Remote - International") is False
