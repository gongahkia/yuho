# Reworked example for S415 Cheating Statute

![](./asset/monkey.jpg)

Here's the process of breaking down a statute's definition. The below example is done on the offense of Cheating under Penal Code S415.

In plaintext, Penal Code S415 is as below.

```txt
"Whoever, by deceiving any person, whether or not such deception was the sole or main inducement, fraudulently or dishonestly induces the person so deceived to deliver or cause the delivery of any property to any person, or to consent that any person shall retain any property, or intentionally induces the person so deceived to do or omit to do anything which he would not do or omit to do if he were not so deceived, and which act or omission causes or is likely to cause damage or harm to any person in body, mind, reputation or property, is said to cheat."
```

When including indentation to conceptually represent each idea introduced, the statute can be logically formatted as follows.

```txt
"Whoever, by deceiving any person, 
WHETHER OR NOT such deception was the sole or main inducement,
    fraudulently OR dishonestly induces the person so deceived
        to deliver any property to any person,
        OR to consent that any person shall retain any property,
    OR intentionally induces the person so deceived
        to do
        OR omit to do anything which he would not do
        OR omit if he were not so deceived
    AND which act or omission
        causes
        OR is likely to cause
            damage
            OR harm
        to that person in body, mind, reputation, or property,
is said to cheat."
```

Once converted to Yuho's syntax, the statute will be structured as follows.

> [!NOTE]
> For an annotated version of the below Yuho code, see [s415_cheating_definition.yh](./../example/cheating/s415_cheating_definition.yh).  

```yh
scope s415CheatingDefinition {

    struct Party { 
        Accused,
        Victim,
    }

    struct AttributionType { 
        SoleInducment,
        NotSoleInducement,
        NA,
    }

    struct DeceptionType { 
        Fraudulently,
        Dishonestly,
        NA,
    }

    struct InducementType { 
        DeliverProperty,
        ConsentRetainProperty,
        DoOrOmit,
        NA,
    }

    struct DamageHarmType { 
        Body,
        Mind, 
        Reputation,
        Property,
        NA,
    }

    struct ConsequenceDefinition { 
        SaidToCheat,
        NotSaidToCheat,
    }

    struct Cheating { 
        string || Party accused,
        string action,
        string || Party victim,
        AttributionType attribution,
        DeceptionType deception,
        InducementType inducement,
        boolean causesDamageHarm,
        {DamageHarmType} || DamageHarmType damageHarmResult, 
        ConsequenceDefinition definition,
    }

    Cheating cheatingDefinition := { 

        accused := Party.Accused,
        action := "deceiving",
        victim := Party.Victim,
        attribution := AttributionType.SoleInducment or AttributionType.NotSoleInducement or AttributionType.NA,
        deception := DeceptionType.Fraudulently or DeceptionType.Dishonestly or DeceptionType.NA,
        inducement := InducementType.DeliverProperty or InducementType.ConsentRetainProperty or InducementType.DoOrOmit or InducementType.NA, 
        causesDamageHarm := TRUE or FALSE,
        damageHarmResult := {
            DamageHarmType.Body,
            DamageHarmType.Mind,
            DamageHarmType.Reputation,
            DamageHarmType.Property,
        } or DamageHarmType.NA, 

        definition := match attribution {
            case AttributionType.SoleInducment := deception
            case AttributionType.NotSoleInducement := deception
            case AttributionType.NA := consequence ConsequenceDefinition.NotSaidToCheat
        },
        definition := match deception {
            case DeceptionType.Fraudulently := consequence inducement
            case DeceptionType.Dishonestly := consequence inducement
            case DeceptionType.NA := consequence ConsequenceDefinition.NotSaidToCheat
        },
        definition := match inducement {
            case InducementType.DeliverProperty := consequence causesDamageHarm
            case InducementType.ConsentRetainProperty := consequence causesDamageHarm
            case InducementType.DoOrOmit := consequence causesDamageHarm
            case InducementType.NA := consequence ConsequenceDefinition.NotSaidToCheat
        },
        definition := match causesDamageHarm {
            case TRUE := consequence damageHarmResult
            case FALSE := consequence ConsequenceDefinition.NotSaidToCheat
        },
        definition := match {
            case DamageHarmType.NA in damageHarmResult := consequence ConsequenceDefinition.NotSaidToCheat
            case _ :=  consequence ConsequenceDefinition.SaidToCheat 
        },

    }

}
```

This struct can then be transpiled to diagrammatic representations with tools like Mermaid.  

Right now two primary Mermaid outputs are supported.  

1. Mindmap
    * show all key elements of a statute at a glance
    * generated by parsing a struct instance

```mermaid
mindmap
    Cheating
      Accused: Party.Accused
      Action: Deceiving
      Victim: Party.Victim
      Attribution
        AttributionType.SoleInducment
        AttributionType.NotSoleInducement
        AttributionType.NA
      Deception
        DeceptionType.Fraudulently
        DeceptionType.Dishonestly
        DeceptionType.NA
      Inducement
        InducementType.DeliverProperty
        InducementType.ConsentRetainProperty
        InducementType.DoOrOmit
        InducementType.NA
      Causes Damage/Harm
        TRUE
        FALSE
      Damage/Harm Result
        DamageHarmType.Body
        DamageHarmType.Mind
        DamageHarmType.Reputation
        DamageHarmType.Property
        DamageHarmType.NA
      Definition
        ConsequenceDefinition.SaidToCheat
        ConsequenceDefinition.NotSaidToCheat
```
2. Flowchart
    * splay out all possible consequences of a statute
    * generated by parsing a struct instance

```mermaid
flowchart TD
    A[Cheating] --> B[Accused := Party.Accused]
    B --> C[Action := Deceiving] 
    C --> D[Victim := Party.Victim]
    D --> E[Attribution]
    E --> |AttributionType.SoleInducement| F[Deception]
    E --> |AttributionType.NotSoleInducement| F
    E --> |AttributionType.NA| Z
    F --> |DeceptionType.Fraudulently| G[Inducement] 
    F --> |DeceptionType.Dishonestly| G
    F --> |DeceptionType.NA| Z
    G --> |InducementType.DeliverProperty| H[CausesDamageHarm]
    G --> |InducementType.ConsentRetainProperty| H
    G --> |InducementType.DoOrOmit| H
    G --> |InducementType.NA| Z
    H --> |TRUE| I[DamageHarmResult]
    H --> |FALSE| Z[ConsequenceDefinition.NotSaidToCheat]
    I --> |DamageHarmType.Body| Y[ConsequenceDefinition.SaidToCheat]
    I --> |DamageHarmType.Mind| Y
    I --> |DamageHarmType.Reputation| Y
    I --> |DamageHarmType.Property| Y
    I --> |DamageHarmType.NA| Z
```

Further, Yuho's flexible syntax also affords separation of concepts foundational to Criminal Law, such as *Material facts*, *Mens Rea* and *Actus Reus*.  

> [!NOTE]
> For an annotated version of the below Yuho code, see [s415_detailed_cheating_definition.yh](./../example/cheating/s415_detailed_cheating_definition.yh).  

```yh
scope s415DetailedCheatingDefinition {

    struct Party {
        Accused,
        Victim,
    }

    struct AttributionType {
        SoleInducment,
        NotSoleInducement,
        NA,
    }

    struct DeceptionType {
        Fraudulently,
        Dishonestly,
        NA,
    }

    struct InducementType {
        DeliverProperty,
        ConsentRetainProperty,
        DoOrOmit,
        NA,
    }

    struct DamageHarmType {
        Body,
        Mind, 
        Reputation,
        Property,
        NA,
    }

    struct ConsequenceDefinition {
        SaidToCheat,
        NotSaidToCheat,
    }

    struct Facts {
        string || Party accused,
        string action,
        string || Party victim,
    }

    struct MentalElement {
        DeceptionType deception,
    }

    struct PhysicalElement {
        AttributionType attribution,
        InducementType inducement,
        boolean causesDamageHarm,
        {DamageHarmType} || DamageHarmType damageHarmResult, 
    }

    struct Cheating {
        Facts materialFacts,
        MentalElement mensRea,
        PhysicalElement actusReus,
        ConsequenceDefinition definition,
    }

    Cheating cheatingDefinition := { 

        materialFacts := {
            accused := Party.Accused,
            action := "deceiving",
            victim := Party.Victim,
        },
        mensRea := {
            deception := DeceptionType.Fraudulently or DeceptionType.Dishonestly or DeceptionType.NA,
        },
        actusReus := {
            attribution := AttributionType.SoleInducment or AttributionType.NotSoleInducement or AttributionType.NA,
            inducement := InducementType.DeliverProperty or InducementType.ConsentRetainProperty or InducementType.DoOrOmit or InducementType.NA, 
            causesDamageHarm := TRUE or FALSE,
            damageHarmResult := {
                DamageHarmType.Body,
                DamageHarmType.Mind,
                DamageHarmType.Reputation,
                DamageHarmType.Property,
            } or DamageHarmType.NA, 
        },

        definition := match attribution {
            case AttributionType.SoleInducment := deception
            case AttributionType.NotSoleInducement := deception
            case AttributionType.NA := consequence ConsequenceDefinition.NotSaidToCheat
        },
        definition := match deception {
            case DeceptionType.Fraudulently := consequence inducement
            case DeceptionType.Dishonestly := consequence inducement
            case DeceptionType.NA := consequence ConsequenceDefinition.NotSaidToCheat
        },
        definition := match inducement {
            case InducementType.DeliverProperty := consequence causesDamageHarm
            case InducementType.ConsentRetainProperty := consequence causesDamageHarm
            case InducementType.DoOrOmit := consequence causesDamageHarm
            case InducementType.NA := consequence ConsequenceDefinition.NotSaidToCheat
        },
        definition := match causesDamageHarm{
            case TRUE := consequence damageHarmResult
            case FALSE := consequence ConsequenceDefinition.NotSaidToCheat
        },
        definition := match {
            case DamageHarmType.NA in damageHarmResult := consequence ConsequenceDefinition.NotSaidToCheat
            case _ :=  consequence ConsequenceDefinition.SaidToCheat 
        },

    }

}
```

When transpiled, these can then be displayed both as a mindmap    

```mermaid
mindmap
    Cheating
        Material facts
            Accused: Party.Accused
            Action: Deceiving
            Victim: Party.Victim
        Mens Rea
            Deception
                DeceptionType.Fraudulently
                DeceptionType.Dishonestly
                DeceptionType.NA
        Actus Reus
            Attribution
                AttributionType.SoleInducment
                AttributionType.NotSoleInducement
                AttributionType.NA
            Inducement
                InducementType.DeliverProperty
                InducementType.ConsentRetainProperty
                InducementType.DoOrOmit
                InducementType.NA
            Causes Damage/Harm
                TRUE
                FALSE
            Damage/Harm Result
                DamageHarmType.Body
                DamageHarmType.Mind
                DamageHarmType.Reputation
                DamageHarmType.Property
                DamageHarmType.NA
      Definition
        ConsequenceDefinition.SaidToCheat
        ConsequenceDefinition.NotSaidToCheat
```

and as a flowchart.

```mermaid
flowchart LR
    A[Cheating] --> B[Accused := Party.Accused]
    subgraph Material facts
        B --> C[Action := Deceiving] 
        C --> D[Victim := Party.Victim]
    end 
    D --> E[Attribution]
    E --> |AttributionType.SoleInducement| F[Deception]
    E --> |AttributionType.NotSoleInducement| F
    E --> |AttributionType.NA| Z
    F --> |DeceptionType.Fraudulently| G[Inducement] 
    F --> |DeceptionType.Dishonestly| G
    F --> |DeceptionType.NA| Z 
    subgraph Mens Rea
        F
    end
    G --> |InducementType.DeliverProperty| H[CausesDamageHarm]
    G --> |InducementType.ConsentRetainProperty| H
    G --> |InducementType.DoOrOmit| H
    G --> |InducementType.NA| Z
    subgraph Actus Reus
        E
        G
        H
        I
    end
    H --> |TRUE| I[DamageHarmResult]
    H --> |FALSE| Z[ConsequenceDefinition.NotSaidToCheat]
    I --> |DamageHarmType.Body| Y[ConsequenceDefinition.SaidToCheat]
    I --> |DamageHarmType.Mind| Y
    I --> |DamageHarmType.Reputation| Y
    I --> |DamageHarmType.Property| Y
    I --> |DamageHarmType.NA| Z
```

To see how a specific scenario plays out *(see [`cheating_illustration_A.yh`](./../example/cheating/cheating_illustration_A.yh))* according to the statute definition specified earlier, each step in the logical journey can be traced.

```mermaid
flowchart TD

    subgraph flowchart2[Illustration A]
        A1[Cheating] --> B1[Accused := A]
        B1 --> C1[Action := Falsely pretending to be in Government service, intentionally deceiving]
        C1 --> D1[Victim := Z]
        D1 --> E1[Attribution := SoleInducement]
        E1 --> F1[Deception := Dishonestly]
        F1 --> G1[Inducement := ConsentRetainProperty]
        G1 --> H1[Causes Damage/Harm := TRUE]
        H1 --> I1[Damage Harm Result := Property]
        I1 --> J1[Definition := SaidToCheat]

        subgraph MaterialFacts1[Material Facts]
            B1
            C1
            D1
        end

        subgraph MensRea1[Mens Rea]
            F1
        end

        subgraph ActusReus1[Actus Reus]
           E1
           G1
           H1
           I1 
        end
    end

    subgraph flowchart1[Cheating statute Definition]
        A2[Cheating] --> B2[Accused := Party.Accused]
        
        subgraph MaterialFacts2[Material Facts]
            B2 --> C2[Action := Deceiving] 
            C2 --> D2[Victim := Party.Victim]
        end
        
        D2 --> E2[Attribution]
        E2 --> |AttributionType.SoleInducement| F2[Deception]
        E2 --> |AttributionType.NotSoleInducement| F2
        E2 --> |AttributionType.NA| Z
        
        F2 --> |DeceptionType.Fraudulently| G2[Inducement] 
        F2 --> |DeceptionType.Dishonestly| G2
        F2 --> |DeceptionType.NA| Z
        
        subgraph MensRea2[Mens Rea]
            F2
        end
        
        G2 --> |InducementType.DeliverProperty| H2[CausesDamageHarm]
        G2 --> |InducementType.ConsentRetainProperty| H2
        G2 --> |InducementType.DoOrOmit| H2
        G2 --> |InducementType.NA| Z
        
        subgraph ActusReus2[Actus Reus]
            E2
            G2
            H2
            I2
        end
        
        H2 --> |TRUE| I2[DamageHarmResult]
        H2 --> |FALSE| Z[ConsequenceDefinition.NotSaidToCheat]
        I2 --> |DamageHarmType.Body| Y[ConsequenceDefinition.SaidToCheat]
        I2 --> |DamageHarmType.Mind| Y
        I2 --> |DamageHarmType.Reputation| Y
        I2 --> |DamageHarmType.Property| Y
        I2 --> |DamageHarmType.NA| Z
    end

    classDef highlightedPath fill:#77DD77,stroke:#000,stroke-width:2px,color:black;
    class A1,B1,C1,D1,E1,F1,G1,H1,I1,J1 highlightedPath;
    class A2,B2,C2,D2,E2,F2,G2,H2,I2,Y highlightedPath;
    linkStyle 0 stroke:#77DD77,stroke-width:4px;
    linkStyle 1 stroke:#77DD77,stroke-width:4px;
    linkStyle 2 stroke:#77DD77,stroke-width:4px;
    linkStyle 3 stroke:#77DD77,stroke-width:4px;
    linkStyle 4 stroke:#77DD77,stroke-width:4px;
    linkStyle 5 stroke:#77DD77,stroke-width:4px;
    linkStyle 6 stroke:#77DD77,stroke-width:4px;
    linkStyle 7 stroke:#77DD77,stroke-width:4px;
    linkStyle 8 stroke:#77DD77,stroke-width:4px;
    linkStyle 9 stroke:#77DD77,stroke-width:4px;
    linkStyle 10 stroke:#77DD77,stroke-width:4px;
    linkStyle 11 stroke:#77DD77,stroke-width:4px;
    linkStyle 12 stroke:#77DD77,stroke-width:4px;
    linkStyle 13 stroke:#77DD77,stroke-width:4px;
    linkStyle 16 stroke:#77DD77,stroke-width:4px;
    linkStyle 19 stroke:#77DD77,stroke-width:4px;
    linkStyle 28 stroke:#77DD77,stroke-width:4px;
```
