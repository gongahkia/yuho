# ----- required imports -----

import os
import json
import ollama

# ----- helper functions -----

def start_model():
    """
    attempts to start and return an ollama model, else returns none
    """
    try:
        client = ollama.Client()
        return client
    except:
        return None

def write_agent_log(
    entry_prompt,
    agent_response,
    target_filepath
):
    """
    writes log data generated by the agentic workflow to the
    json at the specified filepath
    """
    try:
        wrapper = {
            "entry_prompt": entry_prompt,
            "response": agent_response
        }
        with open(target_filepath, "w") as json_file:
            json.dump(wrapper, json_file, indent=4)
        print(
            f"Data successfully written to JSON at the filepath {target_filepath}."
        )
    except Exception as e:
        print(
            f"Error: Unable to read or write to the JSON at the specified filepath: {e}"
        )


def generate_dsl_code(client, example_statute, example_dsl_code, statute_prompt):
    """
    generates DSL code based on an example DSL code and a separate prompt.
    """

    prompt = f"""
    You are an AI tasked with generating DSL code based on criminal law statutes.

    This example DSL code was generated based on the example statute.

    Example statute:
    
    {example_statute}

    Example DSL code:

    {example_dsl_code}

    Based on the above example, generate new DSL code for the following statute:

    {statute_prompt}
    
    Ensure that the generated code adheres to the syntax specifications of the DSL.
    """

    print(prompt)

    response = client.generate(prompt=prompt, model="codellama")

    print("------")

    print(response)

    response_text = response["response"].strip()

    return response_text


def execute_agentic_workflow(log_filepath, example_statute, example_dsl_code, statute_prompt):
    """
    wrapper function that performs agentic
    validation on the specified data, returning
    a boolean upon function execution state
    """
    client_model = start_model()
    
    if client_model:
        if example_statute and example_dsl_code and statute_prompt:

            generated_dsl_code = generate_dsl_code(client_model, example_statute, example_dsl_code, statute_prompt)
            
            write_agent_log(log_filepath, generated_dsl_code)
        
            return True
        else:

            print("Error: Possibe empty values passed to client model.")
            return False

    else:

        print("Error: Unable to generate ollama model.")
        return False


# ----- sample execution code -----

if __name__ == "__main__":

    TARGET_FILEPATH = "generated_log/log.json"

    example_statute  = "Whoever, by deceiving any person, whether or not such deception was the sole or main inducement, fraudulently or dishonestly induces the person so deceived to deliver or cause the delivery of any property to any person, or to consent that any person shall retain any property, or intentionally induces the person so deceived to do or omit to do anything which he would not do or omit to do if he were not so deceived, and which act or omission causes or is likely to cause damage or harm to any person in body, mind, reputation or property, is said to cheat."

    example_dsl_code = """
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
    """

    input_statute_prompt = "A person is guilty of a public nuisance, who does any act, or is guilty of an illegal omission, which causes any common injury, danger or annoyance to the public, or to the people in general who dwell or occupy property in the vicinity, or which must necessarily cause injury, obstruction, danger or annoyance to persons who may have occasion to use any public right."

    client_model = start_model()

    if client_model:

        print("Generating DSL code now...")
        
        generated_dsl_code = generate_dsl_code(client_model, example_statute, example_dsl_code, input_statute_prompt)
        
        write_agent_log(TARGET_FILEPATH, generated_dsl_code)
        
        print("DSL code generation complete.")
    
    else:

        print("Error: Unable to generate ollama model.")