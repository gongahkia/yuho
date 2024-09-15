sig Duration {}
sig Money {}

sig Punishment {
  imprisonmentDuration: lone Duration,
  fine: lone Money, // Using lone to allow for an optional field
  supplementaryPunishment: lone String // Using lone to allow for an optional field
}

sig PunishmentForTheft {
  ofGeneric: lone Punishment,
  ofMotorVehicle: lone Punishment,
  ofDwellingHouse: lone Punishment,
  ofClerkOrServant: lone Punishment,
  afterPreparationCausingDeath: lone Punishment
}

sig Statute {
  sectionNumber: Int,
  sectionDescription: String,
  definition: String,
  result: lone PunishmentForTheft
}

fact aStatuteOnTheft {
  let p1 = Punishment {
    imprisonmentDuration = Duration,
    fine = none,
    supplementaryPunishment = none
  },
  p2 = Punishment {
    imprisonmentDuration = Duration,
    fine = none,
    supplementaryPunishment = "A person convicted of an offence under this section shall, unless the court for special reasons thinks fit to order otherwise, be disqualified for such period as the court may order from the date of his release from imprisonment from holding or obtaining a driving licence under the Road Traffic Act 1961."
  },
  p3 = Punishment {
    imprisonmentDuration = Duration,
    fine = none,
    supplementaryPunishment = none
  },
  p4 = Punishment {
    imprisonmentDuration = Duration,
    fine = none,
    supplementaryPunishment = none
  },
  p5 = Punishment {
    imprisonmentDuration = Duration,
    fine = none,
    supplementaryPunishment = "caning with not less than 3 strokes"
  },
  pft = PunishmentForTheft {
    ofGeneric = p1,
    ofMotorVehicle = p2,
    ofDwellingHouse = p3,
    ofClerkOrServant = p4,
    afterPreparationCausingDeath = p5
  }
  {
    Statute {
      sectionNumber = 378,
      sectionDescription = "Theft",
      definition = "Whoever, intending to take dishonestly any movable property out of the possession of any person without that person’s consent, moves that property in order to such taking, is said to commit theft.",
      result = pft
    }
  }
}
