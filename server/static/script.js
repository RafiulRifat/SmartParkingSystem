// =====================================
// SMART PARKING LIVE DASHBOARD
// ESP32 + FLASK + RASPBERRY PI CAMERA
// =====================================

const SERVER_URL = "/status";


// =====================================
// CAMERA MEMORY
// =====================================

let lastDisplayedCapture = null;


// =====================================
// UPDATE DASHBOARD
// =====================================

async function updateDashboard() {

    try {

        const response = await fetch(
            SERVER_URL,
            {
                cache: "no-store"
            }
        );


        if (!response.ok) {

            throw new Error(
                "Server returned " +
                response.status
            );

        }


        const data = await response.json();


        console.log(
            "LIVE DATA:",
            data
        );


        // =================================
        // SLOT 1
        // =================================

        updateSlot(
            "slot1",
            "slot1_info",
            data.slot1,
            data.distance1
        );


        const distance1 =
            document.getElementById(
                "distance1"
            );


        if (distance1) {

            distance1.innerHTML =
                Number(
                    data.distance1 ?? 0
                ).toFixed(2);

        }


        // =================================
        // SLOT 2
        // =================================

        updateSlot(
            "slot2",
            "slot2_info",
            data.slot2,
            data.distance2
        );


        const distance2 =
            document.getElementById(
                "distance2"
            );


        if (distance2) {

            distance2.innerHTML =
                Number(
                    data.distance2 ?? 0
                ).toFixed(2);

        }


        // =================================
        // GATE
        // =================================

        const gate =
            document.getElementById(
                "gate"
            );


        if (gate) {

            gate.innerHTML =
                data.gate || "CLOSED";

            updateGateColor(
                data.gate
            );

        }


        // =================================
        // GATE ANIMATION
        // =================================

        const gateAnimation =
            document.getElementById(
                "gate_animation"
            );


        if (gateAnimation) {

            gateAnimation.innerHTML =
                data.gate === "OPEN"
                    ? "🚧⬆️ OPEN"
                    : "🚧 CLOSED";

        }


        // =================================
        // BUZZER
        // =================================

        const buzzer =
            document.getElementById(
                "buzzer"
            );


        if (buzzer) {

            buzzer.innerHTML =
                data.buzzer || "OFF";

        }


        // =================================
        // AVAILABLE
        // =================================

        const available =
            Number(
                data.available ?? 0
            );


        const availableElement =
            document.getElementById(
                "available"
            );


        if (availableElement) {

            availableElement.innerHTML =
                available;

        }


        // =================================
        // OVERVIEW
        // =================================

        const overviewAvailable =
            document.getElementById(
                "overview_available"
            );


        if (overviewAvailable) {

            overviewAvailable.innerHTML =
                available;

        }


        const overviewOccupied =
            document.getElementById(
                "overview_occupied"
            );


        if (overviewOccupied) {

            overviewOccupied.innerHTML =
                Math.max(
                    0,
                    2 - available
                );

        }


        // =================================
        // CARS INSIDE
        // =================================

        const carsInside =
            document.getElementById(
                "cars_inside"
            );


        if (carsInside) {

            carsInside.innerHTML =
                data.inside ?? 0;

        }


        // =================================
        // TOTAL ENTRY
        // =================================

        const totalEntries =
            document.getElementById(
                "total_entries"
            );


        if (totalEntries) {

            totalEntries.innerHTML =
                data.entries ?? 0;

        }


        // =================================
        // TOTAL EXIT
        // =================================

        const totalExit =
            document.getElementById(
                "total_exit"
            );


        if (totalExit) {

            totalExit.innerHTML =
                data.exit ?? 0;

        }


        // =================================
        // PARKING WARNING
        // =================================

        updateParkingWarning(
            available
        );


        // =================================
        // LAST UPDATE
        // =================================

        const lastUpdate =
            document.getElementById(
                "last_update"
            );


        if (lastUpdate) {

            lastUpdate.innerHTML =
                data.last_update ||
                "--:--:--";

        }


        // =================================
        // ESP32 STATUS
        // =================================

        const espStatus =
            document.getElementById(
                "esp_status"
            );


        if (espStatus) {

            espStatus.innerHTML =
                "🟢 ESP32 ONLINE";

        }


        // =================================
        // CAMERA STATUS
        // =================================

        updateCamera(
            data
        );


        // =================================
        // CAMERA CAPTURE
        // =================================

        updateCameraCapture(
            data
        );

    }


    catch (error) {

        console.error(
            "SERVER ERROR:",
            error
        );


        const espStatus =
            document.getElementById(
                "esp_status"
            );


        if (espStatus) {

            espStatus.innerHTML =
                "🔴 ESP32 OFFLINE";

        }


        setCameraOffline();

    }

}


// =====================================
// CAMERA STATUS
// =====================================

function updateCamera(data) {

    const online =
        data.camera_online === true;


    const cameraStatus =
        document.getElementById(
            "camera_status"
        );


    const cameraStatusText =
        document.getElementById(
            "camera_status_text"
        );


    const cameraStreamStatus =
        document.getElementById(
            "camera_stream_status"
        );


    if (online) {

        if (cameraStatus) {

            cameraStatus.innerHTML =
                "🟢 ONLINE";

        }


        if (cameraStatusText) {

            cameraStatusText.innerHTML =
                "🟢 ONLINE";

        }


        if (cameraStreamStatus) {

            cameraStreamStatus.innerHTML =
                "🟢 LIVE / ADMIN";

        }

    }

    else {

        if (cameraStatus) {

            cameraStatus.innerHTML =
                "🔴 OFFLINE";

        }


        if (cameraStatusText) {

            cameraStatusText.innerHTML =
                "🔴 OFFLINE";

        }


        if (cameraStreamStatus) {

            cameraStreamStatus.innerHTML =
                "🔴 OFFLINE";

        }

    }

}


// =====================================
// CAMERA OFFLINE
// =====================================

function setCameraOffline() {

    const cameraStatus =
        document.getElementById(
            "camera_status"
        );


    const cameraStatusText =
        document.getElementById(
            "camera_status_text"
        );


    const cameraStreamStatus =
        document.getElementById(
            "camera_stream_status"
        );


    if (cameraStatus) {

        cameraStatus.innerHTML =
            "🔴 OFFLINE";

    }


    if (cameraStatusText) {

        cameraStatusText.innerHTML =
            "🔴 OFFLINE";

    }


    if (cameraStreamStatus) {

        cameraStreamStatus.innerHTML =
            "🔴 OFFLINE";

    }

}


// =====================================
// CAMERA CAPTURE
// =====================================

function updateCameraCapture(data) {

    const captureUrl =
        data.latest_capture;


    // No capture yet

    if (
        !captureUrl ||
        captureUrl === null ||
        captureUrl === ""
    ) {

        return;

    }


    // =================================
    // DETERMINE EVENT FROM CAPTURE
    // =================================

    const event =
        getEventFromCapture(
            captureUrl,
            data.event
        );


    // =================================
    // UPDATE EVENT TEXT
    // =================================

    updateEventText(
        event
    );


    // =================================
    // UPDATE LAST EVENT
    // =================================

    const lastCameraEvent =
        document.getElementById(
            "last_camera_event"
        );


    if (lastCameraEvent) {

        lastCameraEvent.innerHTML =
            formatEventName(
                event
            );

    }


    // =================================
    // CHECK WHETHER PHOTO CHANGED
    // =================================

    if (
        captureUrl ===
        lastDisplayedCapture
    ) {

        return;

    }


    lastDisplayedCapture =
        captureUrl;


    // =================================
    // DISPLAY PHOTO
    // =================================

    showLatestCapture(
        captureUrl,
        event,
        data.last_update
    );

}


// =====================================
// DETERMINE EVENT FROM PHOTO PATH
// =====================================

function getEventFromCapture(
    captureUrl,
    fallbackEvent
) {

    const url =
        String(
            captureUrl || ""
        ).toLowerCase();


    // Server filename is authoritative

    if (
        url.includes(
            "entry"
        )
    ) {

        return "ENTRY";

    }


    if (
        url.includes(
            "exit"
        )
    ) {

        return "EXIT";

    }


    // Only use ESP32 event as fallback

    const event =
        String(
            fallbackEvent || "NONE"
        ).toUpperCase();


    if (
        event === "ENTRY" ||
        event === "EXIT"
    ) {

        return event;

    }


    return "PARKING EVENT";

}


// =====================================
// EVENT TEXT
// =====================================

function updateEventText(
    event
) {

    const message =
        document.getElementById(
            "camera_event_message"
        );


    if (!message) {

        return;

    }


    if (event === "ENTRY") {

        message.innerHTML =
            "🚗 ENTRY capture available";

    }

    else if (event === "EXIT") {

        message.innerHTML =
            "🚙 EXIT capture available";

    }

    else {

        message.innerHTML =
            "📷 Camera ready";

    }

}


// =====================================
// FORMAT EVENT NAME
// =====================================

function formatEventName(
    event
) {

    if (event === "ENTRY") {

        return "🚗 ENTRY";

    }


    if (event === "EXIT") {

        return "🚙 EXIT";

    }


    return "📷 NONE";

}


// =====================================
// SHOW LATEST CAPTURE
// =====================================

function showLatestCapture(
    captureUrl,
    event,
    captureTime
) {

    const section =
        document.getElementById(
            "capture_section"
        );


    const image =
        document.getElementById(
            "latest_capture"
        );


    const link =
        document.getElementById(
            "capture_link"
        );


    const eventText =
        document.getElementById(
            "capture_event"
        );


    const timeText =
        document.getElementById(
            "capture_time"
        );


    const photoStatus =
        document.getElementById(
            "latest_photo_status"
        );


    if (!image) {

        return;

    }


    // =================================
    // CACHE BUSTER
    // =================================

    image.src =
        captureUrl +
        (
            captureUrl.includes("?")
                ? "&"
                : "?"
        ) +
        "t=" +
        Date.now();


    // =================================
    // FULL IMAGE LINK
    // =================================

    if (link) {

        link.href =
            captureUrl;

    }


    // =================================
    // EVENT
    // =================================

    if (eventText) {

        if (event === "ENTRY") {

            eventText.innerHTML =
                "🚗 ENTRY CAPTURE";

        }

        else if (event === "EXIT") {

            eventText.innerHTML =
                "🚙 EXIT CAPTURE";

        }

        else {

            eventText.innerHTML =
                "📸 PARKING EVENT";

        }

    }


    // =================================
    // TIME
    // =================================

    if (timeText) {

        timeText.innerHTML =
            captureTime
                ? "Captured at: " +
                  captureTime
                : "";

    }


    // =================================
    // PHOTO STATUS
    // =================================

    if (photoStatus) {

        photoStatus.innerHTML =
            "📸 Available";

    }


    // =================================
    // SHOW SECTION
    // =================================

    if (section) {

        section.style.display =
            "block";

    }

}


// =====================================
// SLOT STATUS
// =====================================

function updateSlot(
    slotId,
    infoId,
    status,
    distance
) {

    const slot =
        document.getElementById(
            slotId
        );


    const info =
        document.getElementById(
            infoId
        );


    if (!slot) {

        return;

    }


    slot.classList.remove(
        "slot-available",
        "slot-occupied",
        "slot-waiting"
    );


    if (
        status === "OCCUPIED"
    ) {

        slot.innerHTML =
            "🔴 OCCUPIED";


        slot.classList.add(
            "slot-occupied"
        );


        if (info) {

            info.innerHTML =
                "Vehicle Parked (" +
                Number(
                    distance ?? 0
                ).toFixed(2) +
                " cm)";

        }

    }

    else if (
        status === "EMPTY"
    ) {

        slot.innerHTML =
            "🟢 AVAILABLE";


        slot.classList.add(
            "slot-available"
        );


        if (info) {

            info.innerHTML =
                "Free Space (" +
                Number(
                    distance ?? 0
                ).toFixed(2) +
                " cm)";

        }

    }

    else {

        slot.innerHTML =
            "🟡 WAITING";


        slot.classList.add(
            "slot-waiting"
        );


        if (info) {

            info.innerHTML =
                "Checking sensor";

        }

    }

}


// =====================================
// PARKING WARNING
// =====================================

function updateParkingWarning(
    available
) {

    const warning =
        document.getElementById(
            "parking_warning"
        );


    if (!warning) {

        return;

    }


    warning.classList.remove(
        "parking-full",
        "parking-space"
    );


    if (available <= 0) {

        warning.innerHTML =
            "⚠️ PARKING FULL";


        warning.classList.add(
            "parking-full"
        );

    }

    else {

        warning.innerHTML =
            "✅ SPACE AVAILABLE";


        warning.classList.add(
            "parking-space"
        );

    }

}


// =====================================
// GATE COLOR
// =====================================

function updateGateColor(
    status
) {

    const element =
        document.getElementById(
            "gate"
        );


    if (!element) {

        return;

    }


    if (
        status === "OPEN"
    ) {

        element.style.color =
            "#22c55e";

    }

    else {

        element.style.color =
            "#f59e0b";

    }

}


// =====================================
// AUTO REFRESH
// =====================================

setInterval(
    updateDashboard,
    1000
);


// =====================================
// FIRST LOAD
// =====================================

updateDashboard();