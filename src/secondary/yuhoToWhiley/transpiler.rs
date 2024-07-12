struct Duration;
struct Money;
struct String;

struct Punishment {
    imprisonment_duration: Option<Duration>,
    fine: Option<Money>,
    supplementary_punishment: Option<String>,
}

struct PunishmentForTheft {
    of_generic: Option<Punishment>,
    of_motor_vehicle: Option<Punishment>,
    of_dwelling_house: Option<Punishment>,
    of_clerk_or_servant: Option<Punishment>,
    after_preparation_causing_death: Option<Punishment>,
}

struct Statute {
    section_number: i32,
    section_description: String,
    definition: String,
    result: Option<PunishmentForTheft>,
}

fn create_punishment(imprisonment: Option<Duration>, fine: Option<Money>, supplementary: Option<String>) -> Punishment {
    Punishment {
        imprisonment_duration: imprisonment,
        fine,
        supplementary_punishment: supplementary,
    }
}

fn create_punishment_for_theft(p1: Punishment, p2: Punishment, p3: Punishment, p4: Punishment, p5: Punishment) -> PunishmentForTheft {
    PunishmentForTheft {
        of_generic: Some(p1),
        of_motor_vehicle: Some(p2),
        of_dwelling_house: Some(p3),
        of_clerk_or_servant: Some(p4),
        after_preparation_causing_death: Some(p5),
    }
}

fn create_statute(section_num: i32, section_desc: &str, def: &str, result: PunishmentForTheft) -> Statute {
    Statute {
        section_number: section_num,
        section_description: section_desc.to_string(),
        definition: def.to_string(),
        result: Some(result),
    }
}

// MAIN EXECUTION CODE

fn main() {
    let p1 = create_punishment(None, None, None);
    let p2 = create_punishment(None, None, Some("A person convicted of an offence under this section..."));
    let p3 = create_punishment(None, None, None);
    let p4 = create_punishment(None, None, None);
    let p5 = create_punishment(None, None, Some("caning with not less than 3 strokes"));
    let pft = create_punishment_for_theft(p1, p2, p3, p4, p5);
    let statute = create_statute(
        378,
        "Theft",
        "Whoever, intending to take dishonestly any movable property out of the possession of any person without that person's consent, moves that property in order to such taking, is said to commit theft.",
        pft,
    );
    println!("{:?}", statute);
}
