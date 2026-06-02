from app.services.csv_utils import from_csv_int, to_csv_int


def test_csv_roundtrip():
    values = [3, 1, 3, 2]
    csv = to_csv_int(values)
    assert csv == "1,2,3"
    assert from_csv_int(csv) == [1, 2, 3]
