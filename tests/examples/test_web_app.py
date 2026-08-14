from unittest.mock import MagicMock, patch

from examples import web_app


def test_entry_point_builds_the_web_front_end():
    # check - the example's whole job is to run the ordinary game behind the
    # server-backed front-end, then hand control to it
    game = MagicMock()
    with patch.object(web_app, "FishE", return_value=game) as fishE:
        web_app.main()

    assert fishE.call_args.kwargs["interfaceType"] == web_app.UIType.WEB
    game.play.assert_called_once_with()


def test_entry_point_announces_no_address_of_its_own(capsys):
    # check - the URL is said by the front-end once its server is bound, so a
    # port that is misspelled or already taken is never preceded here by an
    # address that will never answer
    with patch.object(web_app, "FishE", return_value=MagicMock()):
        web_app.main()

    assert capsys.readouterr().out == ""
