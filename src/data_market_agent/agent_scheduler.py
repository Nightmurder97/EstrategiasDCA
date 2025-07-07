import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Callable, Coroutine, Any, Dict

logger = logging.getLogger(__name__)

class AgentScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}

    def add_job(self, func: Callable[..., Coroutine[Any, Any, Any]], job_id: str, cron_expression: str, *args, **kwargs) -> None:
        """
        Adds a job to the scheduler.

        :param func: The asynchronous function to execute.
        :param job_id: A unique identifier for the job.
        :param cron_expression: A cron expression defining when the job should run.
                                Example: "0 * * * *" (every hour at minute 0)
                                Example: "*/30 * * * *" (every 30 minutes)
        :param args: Positional arguments to pass to the job function.
        :param kwargs: Keyword arguments to pass to the job function.
        """
        if job_id in self.scheduler.get_jobs():
            logger.warning(f"Job with id '{job_id}' already exists. It will be replaced.")
            self.scheduler.remove_job(job_id)

        trigger = CronTrigger.from_crontab(cron_expression)
        self.scheduler.add_job(func, trigger=trigger, id=job_id, args=args, kwargs=kwargs)
        self.jobs[job_id] = func # Store the function for potential manual trigger or inspection
        logger.info(f"Job '{job_id}' scheduled with cron expression: '{cron_expression}'.")

    def remove_job(self, job_id: str) -> None:
        """Removes a job from the scheduler."""
        if job_id in self.scheduler.get_jobs():
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"Job '{job_id}' removed.")
        else:
            logger.warning(f"Job with id '{job_id}' not found.")

    async def run_job_manually(self, job_id: str, *args, **kwargs) -> Any:
        """Runs a registered job function manually."""
        if job_id in self.jobs:
            logger.info(f"Manually running job '{job_id}'...")
            job_func = self.jobs[job_id]
            result = await job_func(*args, **kwargs) # Ensure job_func is awaited
            logger.info(f"Manual run of job '{job_id}' completed.")
            return result
        else:
            logger.error(f"Cannot run job manually: Job with id '{job_id}' not found in registered functions.")
            return None

    def start(self) -> None:
        """Starts the scheduler. This is a blocking call if not run in a separate thread/process."""
        if not self.scheduler.running:
            try:
                self.scheduler.start()
                logger.info("Scheduler started.")
            except (KeyboardInterrupt, SystemExit):
                logger.info("Scheduler stopped by user.")
                self.shutdown()
            except Exception as e:
                logger.error(f"Error starting scheduler: {e}")
                self.shutdown()
        else:
            logger.info("Scheduler is already running.")

    def shutdown(self, wait: bool = True) -> None:
        """Shuts down the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler shut down.")

# Example usage (will be removed or moved later)
async def example_task(message: str):
    logger.info(f"Example task executed with message: {message} at {__import__('datetime').datetime.now()}")
    print(f"Example task: {message}")

async def main():
    # Configure basic logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    scheduler = AgentScheduler()
    # Schedule example_task to run every minute
    scheduler.add_job(example_task, job_id="example_job_1", cron_expression="* * * * *", args=["Hello from scheduler!"])

    # Schedule another task to run every 2 minutes
    scheduler.add_job(example_task, job_id="example_job_2", cron_expression="*/2 * * * *", args=["Another task running!"])

    try:
        scheduler.start() # This will block if run directly.
                          # In a real app, this might run in a background asyncio task or thread.
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    # This __main__ block is for direct testing of the scheduler.
    # In the actual application, the scheduler will be managed by the agent's main process.
    import asyncio
    # To run this example, you would typically do:
    # asyncio.run(main())
    # However, scheduler.start() is blocking. For a FastAPI app, you'd integrate it differently.
    # For now, this just shows the structure.
    print("AgentScheduler defined. To test, uncomment and run `asyncio.run(main())` in a suitable async context.")
    print("Note: APScheduler's AsyncIOScheduler should be run within an asyncio event loop.")

    # Quick test of manual job run
    async def manual_run_test():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        scheduler = AgentScheduler()
        scheduler.add_job(example_task, job_id="manual_test_job", cron_expression="0 0 1 1 *", args=["Manual Test"]) # Dummy cron
        await scheduler.run_job_manually("manual_test_job", message="Manually triggered task")
        # In a real scenario, scheduler.start() would be called elsewhere.
        # For this test, we don't start the scheduler itself.

    asyncio.run(manual_run_test())
