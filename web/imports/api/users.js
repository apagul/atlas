import { Meteor } from 'meteor/meteor';
import { Mongo } from 'meteor/mongo';
import { check } from 'meteor/check';

import { Programs } from './programs.js';
import { Observations } from './observations.js';
import { Sessions } from './sessions.js';

// publish user affiliations
export const Affiliations = new Mongo.Collection('affiliations');

// publish affiliations and useres
if (Meteor.isServer) {

    // users
    Meteor.publish('users', function() {
	if (Roles.userIsInRole(this.userId, 'admin')) {
	    return Meteor.users.find({}, {fields: {profile: 1, emails: 1}});
	} else {
	    // user not authorized
	    this.stop();
	    return;
	}});

    // publications
    Meteor.publish('affiliations', function() {
	return Affiliations.find({});
    });
}

Meteor.methods({
    'users.insert'(email, profile) {
	if (Meteor.isServer) {

	    // create a new user
	    const id = Accounts.createUser({
		email: email,
		profile: profile})

	    // user was sucessfully created
	    if (id) {

		// add to user to users group
		Roles.addUsersToRoles(id, ['users']);

		// create 'general' program for that user
		Meteor.call('programs.insert', 'General', 'general');
		
		// send enrollment email
		Accounts.sendEnrollmentEmail(id);

		
	    } else {
		CoffeeAlerts.error('Unable to create user...');
	    }
	}
    }, 

    'users.remove'(userId) {
	check(userId, String);

	// check that the user is logged in
	if (! Meteor.userId()) {
	    throw new Meteor.Error('not-authorized');
	}

	if (Roles.userIsInRole(Meteor.userId(), 'admin')) {

	    // delete all programs (this should also delete obs and sessions)
	    Programs.remove({owner: userId});

	    // just to be safe, delete all obs and sessions
	    Observations.remove({owner: userId});
	    Sessions.remove({owner: userId});

	    // delete user
	    Meteor.users.remove(userId);
	}
    },

    'users.addToRole'(userId, role) {

	// verify
	check(userId, String);

	// check that the user is logged in
	if (! Meteor.userId()) {
	    throw new Meteor.Error('not-authorized');
	}

	// check that the current-logged in user is admin
	if (Roles.userIsInRole(Meteor.userId(), 'admins')) {

	    // add the user to the role
	    Roles.addUsersToRoles(userId, role);
	}
    },

    'users.removeFromRole'(userId, role) {
	
	// verify
	check(userId, String);

	// check that the user is logged in
	if (! Meteor.userId()) {
	    throw new Meteor.Error('not-authorized');
	}

	// check that the current-logged in user is admin
	if (Roles.userIsInRole(Meteor.userId(), 'admins')) {

	    // add the user to the role
	    Roles.removeUsersFromRoles(userId, role);
	}
    }, 
    
    'affiliations.insert'(name) {

	// validate parameters
	check(name, String);

	// check that the user is logged in
	if (! Meteor.userId()) {
	    throw new Meteor.Error('not-authorized');
	    return;
	}

	// insert affiliations
	Affiliations.insert({
	    name: name,
	});
    },

    'affiliations.remove'(affilId) {
	check(affilId, String);

	// check that the user is logged in
	if (! Meteor.userId()) {
	    throw new Meteor.Error('not-authorized');
	}

	Affiliations.remove(affilId);
    }, 

});

