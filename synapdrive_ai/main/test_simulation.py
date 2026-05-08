from synapdrive_ai.main.integration_runner import SynapDriveExecutor


def run_simulation():
    engine = SynapDriveExecutor()

    print("\n🔬 SynapDrive-AI AGI Simulation\n")
    simulated_bci_input = input(
        "🧠 Enter simulated intent (e.g. 'navigate forward', 'initiate docking'): "
    )
    simulated_image_input = input(
        "👁️  Enter simulated visual label (e.g. 'road', 'hazard', or leave blank): "
    )

    result = engine.run_once(simulated_bci_input, simulated_image_input or None)

    print("\n🧠 AGI Decision Summary:")
    print("------------------------")
    for k, v in result["intent"].items():
        print(f"{k}: {v}")

    print("\n✅ Execution Result:")
    print("--------------------")
    for k, v in result["result"].items():
        print(f"{k}: {v}")

    print("\n📊 Evaluation Metrics:")
    print("----------------------")
    for k, v in result["evaluation"].items():
        print(f"{k}: {v}")

    if result["status"] == "blocked":
        print(f"\n🚫 Safety Blocked Execution:\nReason: {result['reason']}")


if __name__ == "__main__":
    run_simulation()
