import os
import sys

import click

from storybro.play.block_formatter import BlockFormatter
from storybro.play.player import Player
from storybro.play.settings import PlayerSettings
from storybro.utils import yes_no
import os
gcloudCmd = "gcloud"
if os == "nt":
    gcloudCmd = "cmd /c gcloud"

import subprocess

zone = 'europe-west4-a'

from time import sleep

import numpy as np

import tensorflow as tf
import random, time

@click.command()
@click.argument('story-name', required=True)
@click.option('-m', '--model-name', default="model_v5")
@click.option('--memory', type=int)
@click.option('--max-repeats', type=int)
@click.option('--icon-for-input')
@click.option('--top-separator')
@click.option('--bottom-separator')
@click.option('--fill-width', type=int)
@click.option('--force-cpu', '-f', is_flag=True, help="Force the model to run on the CPU")
@click.pass_obj
def play(config,
         story_name,
         model_name,
         memory, max_repeats,
         icon_for_input,
         top_separator, bottom_separator,
         fill_width,
         force_cpu):

    if force_cpu:
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    theip = None
    thename = None
    while theip == None:
        cmd = gcloudCmd + ' compute tpus list'
        #print(cmd)
        check = (subprocess.check_output((cmd + " --zone=us-central1-b").split(' '))).decode("utf-8")
        
        check = check.split('\n')
        for c in check:
            if len(c) < 5:
                check.remove(c)
        cLen = len(check)
        gogo = True
        #print(check)

        try:
            #print(check)
            #print((check[1].split(' '))[-1])
            if 'READY' in check[1] or 'CREATING' in check[1]:
                thename = check[1][0]
                for item in check[1].split(' '):
                    #print(item)

                    item = item.replace(' ', '')
                    #print(item)    
                    if ':' in item:
                        theip = item
                        gogo = False
            if 'STOPPING' in check[1] or 'STOPPED' in check[1]:
                
                cmd = gcloudCmd + " compute tpus delete --quiet " + (check[1].split(' '))[-0] + " --project=coindex-ai-v0"
                check = (subprocess.check_output((cmd + " --zone=us-central1-b").split(' '))).decode("utf-8")
                print('sleep4...')
                #print(check)
        except subprocess.CalledProcessError:
            print('sleep3...')
            gogo = False
            
        except Exception as e:
            print(e)
           
        if cLen <= 1:
            try:
                #print('1 line output...')
                cmd = gcloudCmd + ' compute tpus create --preemptible --network=default --range=10.240.1.0/29 tpu' + str(random.randint(0,1000)) + str(random.randint(0,1000)) + str(random.randint(0,1000)) + str(random.randint(0,1000)) + str(random.randint(0,1000)) + ' --accelerator-type=v3-8 --version=1.15'
                print(cmd)
                check = (subprocess.check_output((cmd + " --zone=us-central1-b").split(' '))).decode("utf-8")
                print(check)
            except subprocess.CalledProcessError:
                print('sleep1...')
                sleep(15)
            except Exception as e:
                print('sleep2...')
                print(e)
                sleep(15)
    print(theip)
    print(1)
    resolver = tf.contrib.cluster_resolver.TPUClusterResolver(tpu="grpc://" + theip)
    try:
      print('Running on TPU ', resolver.cluster_spec().as_dict()['worker'])
    except ValueError:
      raise BaseException('ERROR: Not connected to a TPU runtime; please see the previous cell in this notebook for instructions!')
    
    print(2)
    try:
        tf.contrib.distribute.initialize_tpu_system(resolver)
    except Exception as e:
        print(e)
    print(3)
    strategy = tf.contrib.distribute.TPUStrategy(resolver)
    with strategy.scope(): # creating the model in the TPUStrategy scope means we will train the model on the TPU

        model = config.model_manager.models.get(model_name)
    if not model:
        click.echo(f"Model `{model_name}` is not installed.")
        return

    for name in config.story_manager.stories:
        print(f"- {name}")

    story = config.story_manager.stories.get(story_name)
    if not story:
        #if not yes_no('Story does not exist. Create new story?'):
            #return
        story = config.story_manager.new_story(story_name)

    sys.argv = ['storybro']
    settings = PlayerSettings(memory, max_repeats, icon_for_input, top_separator, bottom_separator, fill_width)
    formatter = BlockFormatter(settings)
    player = Player(strategy, model, story, settings, formatter)
    player.run()
