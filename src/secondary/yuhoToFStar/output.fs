type duration = string
type money = string

type punishment = {
  imprisonmentDuration : duration;
  fine : unit | money;
  supplementaryPunishment : unit | string;
}

type punishmentForTheft = {
  ofGeneric : punishment;
  ofMotorVehicle : punishment;
  ofDwellingHouse : punishment;
  ofClerkOrServant : punishment;
  afterPreparationCausingDeath : punishment;
}

type statute = {
  sectionNumber : int;
  sectionDescription : string;
  definition : string;
  result : punishmentForTheft;
}

let aStatuteOnTheft : statute = {
  sectionNumber = 378;
  sectionDescription = "Theft";
  definition = "Whoever, intending to take dishonestly any movable property out of the possession of any person without that person’s consent, moves that property in order to such taking, is said to commit theft.";
  result = {
    ofGeneric = {
      imprisonmentDuration = "3 year";
      fine = ();
      supplementaryPunishment = ();
    };
    ofMotorVehicle = {
      imprisonmentDuration = "7 year";
      fine = ();
      supplementaryPunishment = "A person convicted of an offence under this section shall, unless the court for special reasons thinks fit to order otherwise, be disqualified for such period as the court may order from the date of his release from imprisonment from holding or obtaining a driving licence under the Road Traffic Act 1961.";
    };
    ofDwellingHouse = {
      imprisonmentDuration = "7 year";
      fine = ();
      supplementaryPunishment = ();
    };
    ofClerkOrServant = {
      imprisonmentDuration = "7 year";
      fine = ();
      supplementaryPunishment = ();
    };
    afterPreparationCausingDeath = {
      imprisonmentDuration = "10 year";
      fine = ();
      supplementaryPunishment = "caning with not less than 3 strokes";
    };
  };
}
