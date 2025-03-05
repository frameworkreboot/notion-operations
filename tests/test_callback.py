# test_callback.py
import logging
from crews.research_crew.crew import ResearchCrew

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_callback():
    thought_process = []
    
    def simple_callback(output):
        logger.debug(f"Callback received: {type(output)}")
        logger.debug(f"Attributes: {dir(output)}")
        thought_process.append(f"Callback received: {str(output)}")
    
    try:
        crew = ResearchCrew()
        researcher = crew.researcher()
        researcher.step_callback = simple_callback
        
        senior_researcher = crew.senior_researcher()
        senior_researcher.step_callback = simple_callback
        
        result = crew.crew().kickoff(inputs={'topic': 'Test topic for callback debugging'})
        
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result attributes: {dir(result)}")
        logger.info(f"Thought process entries: {len(thought_process)}")
        
        for i, thought in enumerate(thought_process):
            logger.info(f"Thought {i}: {thought[:100]}...")
            
        return result, thought_process
    except Exception as e:
        logger.error(f"Error in test: {str(e)}", exc_info=True)
        return None, thought_process

if __name__ == "__main__":
    result, thoughts = test_callback()
    print(f"Captured {len(thoughts)} thought entries")