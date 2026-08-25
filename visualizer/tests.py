from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase
from django.test.client import RequestFactory

from .services import build_dashboard


PARSED_DATA = {
    "root": "/dataset",
    "file_count": 2,
    "files": [
        {
            "path": "Behavioral Data/Session-01.csv", "name": "Session-01.csv",
            "extension": ".csv", "size_bytes": 100, "status": "parsed",
            "data": {"rows": [
                {"thisN": "0", "trials.make_or_miss.keys": "y", "trials.make_or_miss.rt": "1.5"},
                {"thisN": "1", "trials.make_or_miss.keys": "n", "trials.make_or_miss.rt": "2.5"},
            ]},
        },
        {
            "path": "EEG/session.trg", "name": "session.trg", "extension": ".trg",
            "size_bytes": 50, "status": "parsed", "data": {"events": [
                {"time_seconds": 0.0, "sample": 0, "code": None, "label": None},
                {"time_seconds": 2.0, "sample": 512, "code": "8", "label": None},
            ]},
        },
    ],
}


class DashboardDataTests(SimpleTestCase):
    def test_builds_behavior_and_trigger_series(self):
        dashboard = build_dashboard(PARSED_DATA)

        behavior = dashboard["behavioral_sessions"][0]
        trigger = dashboard["trigger_sessions"][0]
        self.assertEqual((behavior["makes"], behavior["misses"]), (1, 1))
        self.assertEqual(behavior["average_reaction_time"], 2.0)
        self.assertEqual(trigger["event_count"], 1)
        self.assertEqual(trigger["code_counts"], {"8": 1})

    @patch("visualizer.views.render", return_value=HttpResponse("ok"))
    @patch("visualizer.views.parse_dataset", return_value=PARSED_DATA)
    def test_dashboard_view_builds_template_context(self, parse, render):
        from .views import dashboard

        response = dashboard(RequestFactory().get("/"))

        self.assertEqual(response.status_code, 200)
        parse.assert_called_once()
        self.assertEqual(render.call_args.args[1], "visualizer/dashboard.html")
        context = render.call_args.args[2]["dashboard"]
        self.assertEqual(context["behavioral_sessions"][0]["name"], "Session-01.csv")
