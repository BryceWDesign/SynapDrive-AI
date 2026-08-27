from synapdrive_ai.main.integration_runner import SynapDriveExecutor


def run_simulation() -> None:
    engine = SynapDriveExecutor(simulate_delay=False)

    print("\nSynapDrive-AI governed simulation\n")
    command = input("Enter a declared text intent (for example 'move left' or 'stop'): ")
    visual = input(
        "Optional declared visual context label (road, hazard, person, vehicle; blank for none): "
    )

    result = engine.run_once(command, visual or None)

    print("\nGoverned decision summary")
    print("-------------------------")
    for key, value in result["intent"].items():
        print(f"{key}: {value}")

    print("\nSimulation result")
    print("-----------------")
    for key, value in result["result"].items():
        print(f"{key}: {value}")

    print("\nAssurance")
    print("---------")
    print(result.get("assurance", {}))

    if result["status"] == "blocked":
        print(f"\nBlocked: {result['reason']}")


if __name__ == "__main__":
    run_simulation()
