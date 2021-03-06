.. _resources-user:

Managing resources via the config repository
============================================

Software Factory features a way to manage user groups,
Git repositories, Gerrit acls, and projects.

The resources mentioned above can be managed (create/delete/update)
with the CI/CD workflow of the config repository.

.. note::

   This feature replaces the legacy managesf REST endpoints for projects,
   memberships and groups. Legacy endpoints will be removed soon.

.. note::

   It is not recommanded to use both, the legacy endpoints and the resources definition
   with the config repository to avoid conflicts.

.. note::

   Only Gerrit and Storyboard are supported via this workflow.

Advantages of managing resources via the config repository
----------------------------------------------------------

Resources are described via a strict YAML format that will reflect
the current state of the resources on the services. For instance
a group described in YAML will be created and provisioned with the
specified users on Gerrit. Any modifications on the group description
will be reflected on Gerrit. So looking at the YAML files you'll
see the real state of SF services like Gerrit.

Furthermore using this config repository leverages the review workflow
through Gerrit so that any modifications on a resource YAML requires
an human review before being applied to the services. And finally
all modifications will be tracked though the Git config repository history.

A SF operator will just needs to approve a resource change and let
the config-update job applies the state to the services.

Some details about the mechanics under the hood
-----------------------------------------------

The config repository is populated by default with a resources directory.
All YAML files that follow the expected format are loaded and taken into
account.

For example to create a group called mygroup. Here is a YAML file that
describe this resource.

.. code-block:: yaml

  resources:
    groups:
      mygroup:
        members:
          - me@domain.com
          - you@domain.com
        description: This is the group mygroup

This file must be named with the extension .yml or .yaml under
the resources directory of the config repository.

Once done::

 * The default config-check job will execute and validate this new
   resource by checking its format.
 * The Verified label will then receive a note from the CI.
 * Everybody with access to the platform can comment and note the change.
 * Users with rights of CR+2 and W+1 can approve the change.
 * Once approved and merged, the config-update job will take care
   of creating the group on services like Gerrit.

It is a good practice to check the output of the validation (config-check job)
and the apply (config-update job).

A more complete example
-----------------------

Below is a YAML file that can be used as a starting point:

.. code-block:: yaml

  resources:
    projects:
      ichiban-cloud:
        description: The best cloud platform engine
        contacts:
          - contacts@ichiban-cloud.io
        source-repositories:
          - ichiban-compute
          - ichiban-storage
        website: http://ichiban-cloud.io
        documentation: http://ichiban-cloud.io/docs
        issue-tracker-url: http://ichiban-cloud.bugtrackers.io
    repos:
      ichiban-compute:
        description: The compute manager of ichiban-cloud
        acl: ichiban-dev-acl
      ichiban-storage:
        description: The storage manager of ichiban-cloud
        acl: ichiban-dev-acl
    acls:
      ichiban-dev-acl:
        file: |
          [access "refs/*"]
            read = group ichiban-core
            owner = group ichiban-ptl
          [access "refs/heads/*"]
            label-Code-Review = -2..+2 group ichiban-core
            label-Code-Review = -2..+2 group ichiban-ptl
            label-Verified = -2..+2 group ichiban-ptl
            label-Workflow = -1..+1 group ichiban-core
            label-Workflow = -1..+1 group ichiban-ptl
            label-Workflow = -1..+0 group Registered Users
            submit = group ichiban-ptl
            read = group ichiban-core
            read = group Registered Users
          [access "refs/meta/config"]
            read = group ichiban-core
            read = group Registered Users
          [receive]
            requireChangeId = true
          [submit]
            mergeContent = false
            action = fast forward only
        groups:
          - ichiban-ptl
          - ichiban-core
    groups:
      ichiban-ptl:
        members:
          - john@ichiban-cloud.io
          - randal@ichiban-cloud.io
        description: Project Techincal Leaders of ichiban-cloud
      ichiban-core:
        members:
          - eva@ichiban-cloud.io
          - marco@ichiban-cloud.io
        description: Project Core of ichiban-cloud

Please note the users mentioned in the groups must have been
connected at least once on your SF platform.

Deleting a resource is as simple as removing it from the resources YAML files.
Updating a resource is as simple as updating it from the resources YAML files.

Keys under each resources' groups are usually used to create and reference (as
unique id) real resources into services. So if you want to rename a resource
you will see that the resource is detected as "Deleted" an a new one will
be detected as "Created". If you intend to do that with the repos' resource then
you have to make sure you have fetch locally your git repo's branches because
the git repo is going to be deleted and created under the new name.

You can find details about resource models :ref:`here <config-resources-model>`

Resource deletion
-----------------

When resources' modifications include the deletion of a resource, the verification
job "config-check" will return a failure if the commit message of the change
does not include the string "sf-resources: allow-delete". This can be seen
as a confirmation from the change's author to be sure resources' deletions are
expected.
