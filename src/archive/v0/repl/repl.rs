extern crate rustyline;
use rustyline::error::ReadlineError;
use rustyline::Editor;

mod parser;

use parser::{parse_program, Statement};

fn process_input(input: &str) {
    match parse_program(input) {
        Ok((_, program)) => {
            println!("Parsed program:");
            for statement in program {
                println!("{:?}", statement);
            }
        }
        Err(err) => println!("Error: {:?}", err),
    }
}

fn start_yuho_repl() -> rustyline::Result<()> {
    let mut rl = Editor::<()>::new();
    loop {
        let readline = rl.readline("Yuho > ");
        match readline {
            Ok(line) => {
                rl.add_history_entry(line.as_str());
                process_input(line.trim());
            }
            Err(ReadlineError::Interrupted) => {
                println!("CTRL-C");
                break;
            }
            Err(ReadlineError::Eof) => {
                println!("CTRL-D");
                break;
            }
            Err(err) => {
                println!("Error: {:?}", err);
                break;
            }
        }
    }
    Ok(())
}

// ----- MAIN EXECUTION CODE -----

fn main() {
    if let Err(err) = start_yuho_repl() {
        eprintln!("Error: {:?}", err);
    }
}
