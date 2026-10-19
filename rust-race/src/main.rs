mod runtime;
mod sim;

use serde_json::{json, Value};
use std::io::{self, BufRead, Read};

fn replay(path: &str) -> Result<(), String> {
    let mut source = String::new();
    if path == "-" {
        io::stdin()
            .read_to_string(&mut source)
            .map_err(|e| e.to_string())?;
    } else {
        source = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    }
    let request: Value = serde_json::from_str(&source).map_err(|e| e.to_string())?;
    let mut simulation = sim::Simulation::from_fixture(&request["fixture"])?;
    let ticks = request["ticks"]
        .as_u64()
        .ok_or("ticks must be a nonnegative integer")?;
    let steps = request["steps"].as_array().cloned().unwrap_or_default();
    let mut samples = Vec::with_capacity(ticks as usize + 1);
    samples.push(json!({"tick":simulation.tick,"observation":simulation.observation(),"raw_state":simulation.raw_state()}));
    for _ in 0..ticks {
        let next_tick = simulation.tick + 1;
        for step in steps
            .iter()
            .filter(|s| s["tick"].as_u64() == Some(next_tick))
        {
            simulation.set_control(
                step["action_id"]
                    .as_str()
                    .ok_or("action_id must be a string")?,
            )?;
        }
        simulation.step(sim::DT)?;
        samples.push(json!({"tick":simulation.tick,"observation":simulation.observation(),"raw_state":simulation.raw_state()}));
    }
    println!(
        "{}",
        json!({"samples":samples,"summary":simulation.summary(),"config":simulation.config(),"reset_events":simulation.reset_events})
    );
    Ok(())
}

fn run() -> Result<(), String> {
    let arguments: Vec<String> = std::env::args().skip(1).collect();
    if arguments.first().map(String::as_str) == Some("--replay") {
        return replay(arguments.get(1).map(String::as_str).unwrap_or("-"));
    }
    let session = arguments
        .windows(2)
        .find(|pair| pair[0] == "--session")
        .map(|pair| pair[1].clone())
        .ok_or("--session is required")?;
    let stdin = io::stdin();
    let mut reader = stdin.lock();
    let mut first = String::new();
    if reader.read_line(&mut first).map_err(|e| e.to_string())? == 0 {
        return Err("Missing initialization message".into());
    }
    let initialize: Value = serde_json::from_str(&first).map_err(|e| e.to_string())?;
    if initialize["session_id"].as_str() != Some(session.as_str())
        || initialize["method"] != "initialize"
    {
        return Err("Invalid initialization message".into());
    }
    drop(reader);
    runtime::run(session, initialize["arguments"]["idle"].clone())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("mcpkart-race: {error}");
        std::process::exit(1);
    }
}
