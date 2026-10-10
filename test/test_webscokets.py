import asyncio
import json
import websockets


ESP32_IP = "192.168.137.25"  # đổi thành IP thật của ESP32
ESP32_PORT = 81

URI = f"ws://{ESP32_IP}:{ESP32_PORT}"


async def send_and_receive(ws, payload):
    message = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":")
    )

    print(f"\n>>> SEND")
    print(message)

    await ws.send(message)

    response = await ws.recv()

    print("<<< RESPONSE")
    print(response)

    return json.loads(response)


async def main():
    print(f"Connecting to {URI}...")

    async with websockets.connect(URI) as ws:
        print("Connected!")

        # =====================================
        # TEST 1: ping
        # =====================================

        response = await send_and_receive(
            ws,
            {
                "v": 1,
                "id": "test-1",
                "to": "esp32",
                "cmd": "ping"
            }
        )

        assert response["ok"] is True
        assert response["id"] == "test-1"

        print("TEST 1 PASSED")

        # =====================================
        # TEST 2: led
        # =====================================

        response = await send_and_receive(
            ws,
            {
                "v": 1,
                "id": "test-2",
                "to": "esp32",
                "cmd": "led",
                "state": "listening"
            }
        )

        assert response["ok"] is True
        assert response["state"] == "listening"

        print("TEST 2 PASSED")

        # =====================================
        # TEST 3: motion
        # =====================================

        response = await send_and_receive(
            ws,
            {
                "v": 1,
                "id": "test-3",
                "to": "esp32",
                "cmd": "motion",
                "name": "nod"
            }
        )

        assert response["ok"] is True
        assert response["name"] == "nod"

        print("TEST 3 PASSED")

        # =====================================
        # TEST 4: invalid LED state
        # =====================================

        response = await send_and_receive(
            ws,
            {
                "v": 1,
                "id": "test-4",
                "to": "esp32",
                "cmd": "led",
                "state": "wrong_state"
            }
        )

        assert response["ok"] is False
        assert response["error"] == "bad_args"

        print("TEST 4 PASSED")

        # =====================================
        # TEST 5: invalid motion
        # =====================================

        response = await send_and_receive(
            ws,
            {
                "v": 1,
                "id": "test-5",
                "to": "esp32",
                "cmd": "motion",
                "name": "dance"
            }
        )

        assert response["ok"] is False
        assert response["error"] == "bad_args"

        print("TEST 5 PASSED")

        # =====================================
        # TEST 6: unknown command
        # =====================================

        response = await send_and_receive(
            ws,
            {
                "v": 1,
                "id": "test-6",
                "to": "esp32",
                "cmd": "hello_robot"
            }
        )

        assert response["ok"] is False
        assert response["error"] == "unknown_cmd"

        print("TEST 6 PASSED")

        # =====================================
        # TEST 7: malformed JSON
        # =====================================

        bad_json = '{"v":1,"id":"test-7","cmd":'

        print("\n>>> SEND INVALID JSON")
        print(bad_json)

        await ws.send(bad_json)

        response = await ws.recv()

        print("<<< RESPONSE")
        print(response)

        response = json.loads(response)

        assert response["ok"] is False
        assert response["error"] == "bad_args"

        print("TEST 7 PASSED")

    print("\n============================")
    print("ALL TESTS PASSED")
    print("============================")


if __name__ == "__main__":
    asyncio.run(main())