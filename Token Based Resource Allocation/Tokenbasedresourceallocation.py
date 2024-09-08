import threading
import heapq
import time
import random
from collections import defaultdict

class ResourceAllocator:
    def __init__(self, num_tokens, preemption_time=10):
        self.num_tokens = num_tokens
        self.available_tokens = num_tokens
        self.token_lock = threading.Lock()
        self.priority_queue = []
        self.waiting_times = defaultdict(list)
        self.queue_condition = threading.Condition()
        self.preemption_time = preemption_time
        self.token_usage = defaultdict(int)
        self.total_tasks = 0
        self.completed_tasks = 0
        self.start_time = time.time()

    def allocate_resource(self, priority=0, timeout=None, task_id=None):
        thread_name = threading.current_thread().name
        request_time = time.time()
        with self.queue_condition:
            entry = (priority, request_time, thread_name, task_id)
            heapq.heappush(self.priority_queue, entry)
            print(f"{thread_name} requested a token with priority {priority} and task ID {task_id}.")

            # Wait for resource allocation based on priority, timeout, and preemption
            start_time = time.time()
            while entry in self.priority_queue:
                elapsed_time = time.time() - start_time
                if timeout is not None and elapsed_time >= timeout:
                    print(f"{thread_name} timed out after {timeout} seconds. Task ID {task_id} timed out.")
                    return None
                if self.available_tokens > 0 and self.priority_queue[0] == entry:
                    self.available_tokens -= 1
                    heapq.heappop(self.priority_queue)
                    self.waiting_times[priority].append(elapsed_time)
                    self.total_tasks += 1
                    print(f"{thread_name} acquired a token with priority {priority}. Task ID {task_id} started.")
                    return entry
                self.queue_condition.wait(timeout - elapsed_time if timeout else None)

    def release_resource(self, entry):
        with self.queue_condition:
            self.available_tokens += 1
            priority, request_time, thread_name, task_id = entry
            self.completed_tasks += 1
            self.token_usage[task_id] += 1
            print(f"{thread_name} released a token. Task ID {task_id} completed. Total tokens: {self.available_tokens}")
            self.queue_condition.notify_all()

    def add_tokens(self, count):
        with self.queue_condition:
            self.num_tokens += count
            self.available_tokens += count
            print(f"Added {count} tokens. Total available: {self.available_tokens}")
            self.queue_condition.notify_all()

    def preempt_task(self, task_id):
        with self.queue_condition:
            print(f"Preempting Task ID {task_id}")
            # Notify other threads
            self.queue_condition.notify_all()

    def monitor_metrics(self):
        with self.queue_condition:
            elapsed_time = time.time() - self.start_time
            avg_wait_times = {priority: sum(times) / len(times) if times else 0 for priority, times in self.waiting_times.items()}
            print(f"Monitoring Metrics after {elapsed_time:.2f} seconds:")
            print(f"Total Tasks: {self.total_tasks}, Completed: {self.completed_tasks}")
            print(f"Average Waiting Times by Priority: {avg_wait_times}")
            print(f"Token Usage by Task ID: {dict(self.token_usage)}")

def task(resource_allocator, priority, timeout, task_id):
    token = resource_allocator.allocate_resource(priority, timeout, task_id)
    if token:
        # Simulate task execution with a random time slice
        task_duration = random.uniform(1, 3)
        print(f"Task {task_id} is executing for {task_duration:.2f} seconds.")
        time.sleep(task_duration)
        resource_allocator.release_resource(token)
    else:
        print(f"Task {task_id} failed to acquire a token.")

if __name__ == "__main__":
    num_tokens = 3  # Initial number of tokens
    resource_allocator = ResourceAllocator(num_tokens, preemption_time=5)

    # Create multiple threads with priorities, timeouts, and task IDs
    threads = []
    task_params = [(1, 5, 'T1'), (2, 3, 'T2'), (0, 4, 'T3'), (3, 1, 'T4'), (2, 2, 'T5')]
    for i, (priority, timeout, task_id) in enumerate(task_params):
        t = threading.Thread(target=task, name=f"Thread-{i+1}", args=(resource_allocator, priority, timeout, task_id))
        threads.append(t)
        t.start()

    # Simulate adding more tokens after some time
    time.sleep(5)
    resource_allocator.add_tokens(2)

    # Preempt a task after some time
    time.sleep(3)
    resource_allocator.preempt_task('T2')

    for t in threads:
        t.join()

    # Print metrics and monitor statistics
    resource_allocator.monitor_metrics()

    print("All tasks completed.")
