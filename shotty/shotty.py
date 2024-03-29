import boto3
import botocore  #enabes try and excpet
#import sys  # in order to read in parameters
import click


session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

#THIS IS THE CODE TO FILTER THE INSTANCES BY PROJECT TAG
def filter_instances(project):
    instances = []

    if project:
         filters = [{'Name':'tag:Project', 'Values':[project]}]
         instances = ec2.instances.filter (Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

@click.group()
def cli():
   """shotty manges snapshots"""

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None, help="Only volumes for project (tag Project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True, help="List all snapshots, not just most recent")
def list_snapshots(project, list_all):
    "List EC2 snapshots"
     
    instances = filter_instances(project) 
    
    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(",  ".join((
                    s.id,
                    v.id,
                    i.id, 
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                    )))
                if s.state=='completed' and not list_all: break   #prints on the most recent snapshot

    return   


@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None, help="Only volumes for project (tag Project:<name>)")

def list_volumes(project):
    "List EC2 volumes"
     
    instances = filter_instances(project) 

    for i in instances:
        for v in i.volumes.all():
            print (",  ".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + " GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"    
            )))

    return


@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('snapshot')
@click.option('--project', default=None, help="Only instances for project (tag Project:<name>)")
def create_snapshots(project):
    "Stop snapshots for EC2 instances"

    instances = filter_instances(project) 

    for i in instances:
        print("Stopping {0}.....".format(i.id))
        
        i.stop()
        i.wait_until_stopped()
        
        for v in i.volumes.all():
            print("Creating snapshot of {0}".format(v.id))
            v.create_snapshot(Description="Created by Snappy")
            
        print("Starting {0}.....".format(i.id))
        
        i.start()
        i.wait_until_running()
    print("Job is done!")
    return

##START OF LIST INSTANCES
@instances.command('list')
@click.option('--project', default=None, help="Only instances for project 9tag Project:<name>)")

def list_instances(project):
    "List EC2 instances"
     
    instances = filter_instances(project) 

    for i in instances:
        tags = {t['Key']: t['Value'] for t in i.tags or []}    #declaring a dictionary t...get all tags for an instance
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>'))))
    return


@instances.command('stop')
@click.option('--project', default=None, help='Only instances for project')

def stop_instances(project):
    "Stop EC2 instances"
    
    instances = filter_instances(project) 

    for i in instances:
        print ("stopping {0}...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Could not start {0}. ".format(i.id) + str(e))
            continue
    return    


@instances.command('start')
@click.option('--project', default=None, help='Only instances for project')

def stop_instances(project):
    "Start EC2 instances"
    
    instances = filter_instances(project) 

    for i in instances:
        print ("starting {0}...".format(i.id))
        
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("Could not start {0}. ".format(i.id) + str(e))
            continue
   
    return    

if __name__== '__main__':
   # print (sys.argv) 
     cli()

