import json
from .models import Frame, Record
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def index(request):
    """View function for home page of site."""

    # Count objects.
    frames = Frame.objects
    num_move = frames.filter(mode="m").count()
    num_click = frames.filter(mode="c").count()
    num_scroll = frames.filter(mode="s").count()
    records = Record.objects.all()

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        "mouse/index.html",
        context={
            "num_move": num_move,
            "num_click": num_click,
            "num_scroll": num_scroll,
            "records": records,
        },
    )


def play(request):
    """View function for playback page of recordings."""
    return render(request, "mouse/play.js", context={})


def set_record(request):
    """Store one mouse recording."""
    data = json.loads(request.POST.get("data"))
    user_agent = {}
    for attr in dir(request.user_agent):
        # Exclude private variables.
        if not "_" == attr[0]:
            # Exclude complex objects.
            if attr != "browser" and attr != "os" and attr != "device":
                user_agent[attr] = getattr(request.user_agent, attr)
    if data:
        window = data["window"]
        rec = Record(
            time=float(data["timeElapsed"]),
            width=int(window["width"]),
            height=int(window["height"]),
            **user_agent,
        )
        rec.save()
        for frame in data["frames"]:
            Frame(mode=frame[0], x=frame[1], y=frame[2], record=rec).save()

    # No Content, according to https://www.w3.org/TR/beacon/#sec-sendBeacon-method.
    return HttpResponse(status=204)


def get_record(request):
    """Return requested mouse recording."""
    request = request.GET
    if request and request["id"]:
        record = Record.objects.get(id=request["id"])
        return JsonResponse(
            {
                "success": True,
                "data": {
                    "frames": [
                        [frame.mode, frame.x, frame.y]
                        for frame in record.frame_set.all()
                    ],
                    "timeElapsed": record.time,
                    "window": {"width": record.width, "height": record.height},
                },
            }
        )
    return JsonResponse({"success": False})
