from vera.governance.signing import artifact_digest, sign_artifact


def test_sign_artifact_digest_stable():
    d1 = artifact_digest({"a": 1})
    d2 = artifact_digest({"a": 1})
    assert d1 == d2
    sig = sign_artifact({"a": 1})
    assert sig["digest"] == f"sha256:{d1}"
