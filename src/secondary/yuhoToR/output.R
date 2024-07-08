# struct definition

aStatuteOnTheft <- list(
  sectionNumber = 378,
  sectionDescription = "Theft",
  definition = "Whoever, intending to take dishonestly any movable property out of the possession of any person without that person’s consent, moves that property in order to such taking, is said to commit theft.",
  result = list(
    ofGeneric = list(
      imprisonmentDuration = 3,
      fine = NULL,
      supplementaryPunishment = NULL
    ),
    ofMotorVehicle = list(
      imprisonmentDuration = 7,
      fine = NULL,
      supplementaryPunishment = "A person convicted of an offence under this section shall, unless the court for special reasons thinks fit to order otherwise, be disqualified for such period as the court may order from the date of his release from imprisonment from holding or obtaining a driving licence under the Road Traffic Act 1961."
    ),
    ofDwellingHouse = list(
      imprisonmentDuration = 7,
      fine = NULL,
      supplementaryPunishment = NULL
    ),
    ofClerkOrServant = list(
      imprisonmentDuration = 7,
      fine = NULL,
      supplementaryPunishment = NULL
    ),
    afterPreparationCausingDeath = list(
      imprisonmentDuration = 10,
      fine = NULL,
      supplementaryPunishment = "caning with not less than 3 strokes"
    )
  )
)

# main execution code

print(aStatuteOnTheft)
