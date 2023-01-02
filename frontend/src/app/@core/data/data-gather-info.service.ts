import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';

// Dialog
import { NbDialogService } from '@nebular/theme';
import { ModalDialogComponent } from '../../pages/shared/modal-dialog/modal-dialog.component';

// RxJS
import { takeWhile } from 'rxjs/operators' ;
import { Observable } from 'rxjs/Observable';
import { mergeMap } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { ToasterConfig } from 'angular2-toaster';
import 'style-loader!angular2-toaster/toaster.css';
import { NbGlobalLogicalPosition, NbGlobalPhysicalPosition, NbGlobalPosition, NbToastrService, NbComponentStatus } from '@nebular/theme';
// import { NbToastStatus } from '@nebular/theme/components/toastr/model';

@Injectable({
    providedIn: 'root',
})
export class DataGatherInfoService {

    private data = {};
    private globalGather: any = {};

    private email: string;
    private username: string;
    public  response: any;
    private visualTasks: any;

    constructor(private http: HttpClient,
                private dialogService: NbDialogService,
                private toastrService: NbToastrService) {}

    /* Global Data */
    public initialize() {
        this.globalGather = {};
        console.log('dataService Initialize globalGather :', this.globalGather);
        return this.globalGather;
    }

    public pushGather(key, value) {
        this.globalGather[key] = value;
        console.log('dataService Push globalGather :', this.globalGather);
    }

    public pullGather() {
        console.log('dataService Pull globalGather :', this.globalGather);
        return this.globalGather;
    }

    public removeGather(key) {
        delete this.globalGather[key];
        console.log('dataService Remove globalGather :', this.globalGather);
    }

    /* Http Service */
    // private readonly gatherUrl: string = environment.apiUrl + 'pub/items';
    // TODO : Use environment to set gatherUrl
    private readonly gatherUrl: string = 'http://127.0.0.1:5000/';

    // Get test
    public postTest$(): Observable<any> {
        return this.http.post<any>(this.gatherUrl + 'testing', 1);
    }

    // Get tasklist
    public getTaskList$(): Observable<any> {
        return this.http.get<any>(this.gatherUrl + 'tasklist');
    }

    // Get apikeys
    public getApiKeys$(keys: any): Observable<any> {
        return this.http.post<any>(this.gatherUrl + 'apikey', keys);
    }

    // Generic GET request
    public getRequest$(url: string): Observable<any> {
        return this.http.get<any>(this.gatherUrl + url);
    }

    // Generic POST request
    public postRequest$(module: string, param: any): Observable<any> {
        return this.http.post<any>(this.gatherUrl + module, param);
    }

    // Generic POST and GET request
    public executeRequest$(module: string, param: any): Observable<any> {
        return this.http.post<any>(this.gatherUrl + module, param)
                   .pipe(mergeMap(task => this.getRequestResult$('result/' + task.task, task)));
    }
    // GET request result
    public getRequestResult$(url: string, task: any): Observable<any> {
        for (let indexTaskexec in this.globalGather['taskexec']) {
            if (this.globalGather['taskexec'][indexTaskexec].module == task.module && 
                this.globalGather['taskexec'][indexTaskexec].param == task.param) {

                this.globalGather['taskexec'][indexTaskexec].task_id = task.task;
                this.globalGather['taskexec'][indexTaskexec].state = 'PROCESS';
                // console.log("State change..................");
            }
        }

        return this.http.get<any>(this.gatherUrl + url);
    }

    // Is the email valid format
    public isValidFormatEmail(email) {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }

    // Validate email
    public validateEmail(email) {

        console.log('validateEmail func', email);
        if (this.isValidFormatEmail(email)) {
            // Execute gatherer
            this.pushGather('email', email);
            this.gathererInfo(email);
            // this.fakeGather();
        } else {
            // Launch Dialog
            this.openDialogError('Invalid e-mail', 'You must enter a valid e-mail address to gather information');
        }
        return this.globalGather;
    }

    /* Dialog */
    public openDialogError(title, text) {
        this.dialogService.open(ModalDialogComponent, {
            context: {
                title: title,
                text: text,
            },
            hasBackdrop: true,
        });
    }

    /* Gather Info */
    public gathererInfo(email: string) {

        this.email = email;
        // Split email in username and domain
        this.username = email.split('@')[0];
        this.globalGather['taskexec'] = [];
        // Process PENDING // Process SUCCESS // Process ERROR
        this.globalGather['taskresume'] = [{PP: 0, PS: 0, PE: 0}];
        console.log('Username : ', this.username);

        // Generic executer
        // this.showToast('info', 'Tasklist', 'Send Tasklist process');
        this.getTaskList$()
            .subscribe(this.processTasklist,
                       err => console.error('Ops: ', err.message),
        );

        // EmailRepIO
        if (this.isModuleParamRunTaskExec('emailrep', this.email, 'User', 100)) {
            // KKK this.showToast(NbToastStatus.INFO, 'EmailRepIO', 'Send information gathering');
            this.showToast('info', 'EmailRepIO', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('emailrep', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'User', 'emailrep', this.email),
                           () => console.log('Completed EmailRep'),
            );
        }

        // Leaklookup
        if (this.isModuleParamRunTaskExec('leaklookup', this.email, 'User', 100)) {
            this.showToast('info', 'LeakLookup', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('leaklookup', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'User', 'leaklookup', this.email),
                           () => console.log('Completed Leaklookup'),
            );
        }

        // Dorks
        if (this.isModuleParamRunTaskExec('dorks', this.username, 'iKy', 1)) {
            this.showToast('info', 'Dorks', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('dorks', {username: this.username, dorks: '', from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'dorks', this.username),
                           () => console.log('Completed Dorks'),
            );
        }

        // Search
        if (this.isModuleParamRunTaskExec('search', this.username, 'iKy', 1)) {
            this.showToast('info', 'Searchers', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('search', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'search', this.username),
                           () => console.log('Completed Searchers'),
            );
        }

        // // Sherlock (Temporary disable)
        // if (this.isModuleParamRunTaskExec('sherlock', this.username, 'iKy', 1)) {
        //     this.showToast('info', 'Sherlock', 'Send information gathering');
        //     this.globalGather['taskresume'][0].PP++;
        //     this.executeRequest$('sherlock', {username: this.username, from: 'iKy'})
        //         .subscribe(this.processResponse,
        //                    // err => console.error('Ops: ', err.message),
        //                    err => this.processRetry(err, 'iKy', 'sherlock', this.username),
        //                    () => console.log('Completed Sherlock'),
        //     );
        // }

        // Holehe
        if (this.isModuleParamRunTaskExec('holehe', this.email, 'User', 100)) {
            this.showToast('info', 'Holehe', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('holehe', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'User', 'holehe', this.email),
                           () => console.log('Completed Holehe'),
            );
        }

        // Fullcontact
        if (this.isModuleParamRunTaskExec('fullcontact', this.email, 'User', 100)) {
            this.showToast('info', 'Fullcontact', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('fullcontact', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'User', 'fullcontact', this.email),
                           () => console.log('Completed Fullcontact'),
            );
        }

        // Peopledatalabs
        if (this.isModuleParamRunTaskExec('peopledatalabs', this.email, 'User', 100)) {
            this.showToast('info', 'Peopledatalabs', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('peopledatalabs', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'User', 'peopledatalabs', this.email),
                           () => console.log('Completed Peopledatalabs'),
            );
        }

        // Github
        if (this.isModuleParamRunTaskExec('github', this.username, 'iKy', 1)) {
            this.showToast('info', 'GitHub', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('github', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'github', this.username),
                           () => console.log('Completed GitHub'),
            );
        }

        // // Ghostproject TODO : Repair
        // this.showToast(NbToastStatus.INFO, 'Ghostproject', 'Send information gathering');
        // this.executeRequest$('ghostproject', {username: this.email, from: 'Initial'})
        //         .subscribe(this.processResponse,
        //                    err => console.error('Ops: ', err.message),
        //                    () => console.log('Completed ghostproject')
        // );

        // Linkedin
        // if (this.isModuleParamRunTaskExec('linkedin', this.email, 'User', 100)) {
        //     this.showToast('info', 'Linkedin', 'Send information gathering');
        //     this.globalGather['taskresume'][0].PP++;
        //     this.executeRequest$('linkedin', {username: this.email, from: 'User'})
        //             .subscribe(this.processResponse,
        //                        err => console.error('Ops: ', err.message),
        //                        () => console.log('Completed linkedin')
        //     );
        // };

        // Keybase
        if (this.isModuleParamRunTaskExec('keybase', this.username, 'iKy', 1)) {
            this.showToast('info', 'Keybase', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('keybase', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'keybase', this.username),
                           () => console.log('Completed Keybase'),
            );
        }

        // Leaks
        if (this.isModuleParamRunTaskExec('leaks', this.email, 'User', 100)) {
            this.showToast('info', 'Leaks (HIBP)', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('leaks', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'User', 'leaks', this.email),
                           () => console.log('Completed Leaks (HIBP)'),
            );
        }

        // Darkpass
        if (this.isModuleParamRunTaskExec('darkpass', this.email, 'User', 100)) {
            this.showToast('info', 'Darkpass (Darknet)', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('darkpass', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'User', 'darkpass', this.email),
                           () => console.log('Completed Darkpass (Darknet)'),
            );
        }

        // SocialScan
        if (this.isModuleParamRunTaskExec('socialscan', this.email, 'User', 100)) {
            this.showToast('info', 'SocialScan', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('socialscan', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'User', 'socialscan', this.email),
                           () => console.log('Completed SocialScan'),
            );
        }

        // Tiktok
        if (this.isModuleParamRunTaskExec('tiktok', this.username, 'iKy', 1)) {
            this.showToast('info', 'Tiktok', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('tiktok', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'tiktok', this.username),
                           () => console.log('Completed Tiktok'),
            );
        }

        // // Skype (decprecated)
        // if (this.isModuleParamRunTaskExec('skype', this.email, 'User', 100)) {
        //     this.showToast('info', 'Skype', 'Send information gathering');
        //     this.globalGather['taskresume'][0].PP++;
        //     this.executeRequest$('skype', {username: this.email, from: 'User'})
        //             .subscribe(this.processResponse,
        //                        err => console.error('Ops: ', err.message),
        //                        () => console.log('Completed Skype'),
        //     );
        // }

        // Venmo
        if (this.isModuleParamRunTaskExec('venmo', this.username, 'iKy', 1)) {
            this.showToast('info', 'Venmo', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('venmo', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'venmo', this.username),
                           () => console.log('Completed Venmo'),
            );
        }

        // Tinder
        if (this.isModuleParamRunTaskExec('tinder', this.username, 'iKy', 1)) {
            this.showToast('info', 'Tinder', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('tinder', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'tinder', this.username),
                           () => console.log('Completed Tinder'),
            );
        }

        // Reddit
        if (this.isModuleParamRunTaskExec('reddit', this.username, 'iKy', 1)) {
            this.showToast('info', 'Reddit', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('reddit', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'reddit', this.username),
                           () => console.log('Completed Reddit'),
            );
        }

        // Spotify
        if (this.isModuleParamRunTaskExec('spotify', this.username, 'iKy', 1)) {
            this.showToast('info', 'Spotify', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('spotify', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'spotify', this.username),
                           () => console.log('Completed Spotify'),
            );
        }

        // Twitch
        if (this.isModuleParamRunTaskExec('twitch', this.username, 'iKy', 1)) {
            this.showToast('info', 'Twitch', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('twitch', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'twitch', this.username),
                           () => console.log('Completed Twitch'),
            );
        }

        // Mastodon
        if (this.isModuleParamRunTaskExec('mastodon', this.username, 'iKy', 1)) {
            this.showToast('info', 'Mastodon', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('mastodon', {username: this.username, from: 'iKy'})
                .subscribe(this.processResponse,
                           // err => console.error('Ops: ', err.message),
                           err => this.processRetry(err, 'iKy', 'mastodon', this.username),
                           () => console.log('Completed Mastodon'),
            );
        }

    }

    /* Gather Info Advance */
    public gathererInfoAdvance(data: string) {

        this.pushGather('data', data);
        this.pushGather('email', data); // Temporary fix
        let datas = data;
        this.globalGather['taskexec'] = [];
        // Process PENDING // Process SUCCESS // Process ERROR
        this.globalGather['taskresume'] = [{PP: 0, PS: 0, PE: 0}];
        console.log('====================================================');
        console.log('Datas : ', datas);

        // Generic executer
        // this.showToast('info', 'Tasklist', 'Send Tasklist process');
        this.getTaskList$()
            .subscribe(this.processTasklist,
                       err => console.error('Ops: ', err.message),
        );

        // Evaluation of datas
        if (datas['twitter'] !== '') {
            console.log('Twitter : ', datas['twitter']);
            // twitter
            if (this.isModuleParamRunTaskExec('twitter', datas['twitter'], 'User', 100)) {
                this.showToast('info', 'twitter', 'send information gathering');
                this.globalGather['taskresume'][0].pp++;
                this.executeRequest$('twitter', {username: datas['twitter'], from: 'user'})
                    .subscribe(this.processResponse,
                               // err => console.error('ops: ', err.message),
                               err => this.processRetry(err, 'User', 'twitter', datas['twitter']),
                               () => console.log('completed twitter'),
                );
            }
            // // twint
            // if (this.isModuleParamRunTaskExec('twint', datas['twitter'], 'user', 100)) {
            //     this.showToast('info', 'twint', 'send information gathering');
            //     this.globalGather['taskresume'][0].pp++;
            //     this.executeRequest$('twint', {username: datas['twitter'], from: 'user'})
            //         .subscribe(this.processResponse,
            //                    err => console.error('ops: ', err.message),
            //                    err => this.processRetry(err, 'User', 'twint', datas['twitter']),
            //                    () => console.log('completed twint'),
            //     );
            // }
        }

        if (datas['linkedin'] !== '') {
            console.log('Linkedin : ', datas['linkedin']);
            // Linkedin
            if (this.isModuleParamRunTaskExec('linkedin', datas['linkedin'], 'User', 100)) {
                this.showToast('info', 'Linkedin', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('linkedin', {username: datas['linkedin'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'linkedin', datas['linkedin']),
                               () => console.log('Completed Linkedin'),
                );
            }
        }

        if (datas['github'] !== '') {
            console.log('Github : ', datas['github']);
            // Github
            if (this.isModuleParamRunTaskExec('github', datas['github'], 'User', 100)) {
                this.showToast('info', 'Github', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                // this.executeRequest$('github', {username: datas['github'], from: 'User'})
                //     .subscribe(this.processResponse,
                //                err => console.error('Ops: ', err.message),
                //                () => console.log('Completed Github'),
                // );
                this.executeRequest$('github', {username: datas['github'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => this.processRetry(err, 'User', 'github', datas['github']),
                               err => this.processRetry(err, 'User', 'github', datas['github']),
                               () => console.log('Completed Github'),
                );
            }
        }

        if (datas['instagram'] !== '') {
            console.log('Instagram : ', datas['instagram']);
            // Instagram
            if (this.isModuleParamRunTaskExec('instagram', datas['instagram'], 'User', 100)) {
                this.showToast('info', 'Instagram', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('instagram', {username: datas['instagram'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'instagram', datas['instagram']),
                               () => console.log('Completed Instagram'),
                );
            }
        }

        if (datas['tiktok'] !== '') {
            console.log('Tiktok : ', datas['tiktok']);
            // Tiktok
            if (this.isModuleParamRunTaskExec('tiktok', datas['tiktok'], 'User', 100)) {
                this.showToast('info', 'TikTok', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('tiktok', {username: datas['tiktok'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'tiktok', datas['tiktok']),
                               () => console.log('Completed Tiktok'),
                );
            }
        }

        if (datas['tinder'] !== '') {
            console.log('Tinder : ', datas['tinder']);
            // Tinder
            if (this.isModuleParamRunTaskExec('tinder', datas['tinder'], 'User', 100)) {
                this.showToast('info', 'Tinder', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('tinder', {username: datas['tinder'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'tinder', datas['tinder']),
                               () => console.log('Completed Tinder'),
                );
            }
        }

        if (datas['venmo'] !== '') {
            console.log('Venmo : ', datas['venmo']);
            // Venmo
            if (this.isModuleParamRunTaskExec('venmo', datas['venmo'], 'User', 100)) {
                this.showToast('info', 'Venmo', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('venmo', {username: datas['venmo'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'venmo', datas['venmo']),
                               () => console.log('Completed Venmo'),
                );
            }
        }

        if (datas['reddit'] !== '') {
            console.log('Reddit : ', datas['reddit']);
            // Reddit
            if (this.isModuleParamRunTaskExec('reddit', datas['reddit'], 'User', 100)) {
                this.showToast('info', 'Reddit', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('reddit', {username: datas['reddit'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'reddit', datas['reddit']),
                               () => console.log('Completed Reddit'),
                );
            }
        }

        if (datas['spotify'] !== '') {
            console.log('Spotify : ', datas['spotify']);
            // Spotify
            if (this.isModuleParamRunTaskExec('spotify', datas['spotify'], 'User', 100)) {
                this.showToast('info', 'Spotify', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('spotify', {username: datas['spotify'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'spotify', datas['spotify']),
                               () => console.log('Completed Spotify'),
                );
            }
        }

        if (datas['twitch'] !== '') {
            console.log('Twitch : ', datas['twitch']);
            // Twitch
            if (this.isModuleParamRunTaskExec('twitch', datas['twitch'], 'User', 100)) {
                this.showToast('info', 'Twitch', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('twitch', {username: datas['twitch'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'twitch', datas['twitch']),
                               () => console.log('Completed Twitch'),
                );
            }
        }

        if (datas['mastodon'] !== '') {
            console.log('Mastodon : ', datas['mastodon']);
            // Mastodon
            if (this.isModuleParamRunTaskExec('mastodon', datas['mastodon'], 'User', 100)) {
                this.showToast('info', 'Mastodon', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('mastodon', {username: datas['mastodon'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'mastodon', datas['mastodon']),
                               () => console.log('Completed Mastodon'),
                );
            }
        }

        if (datas['keybase'] !== '') {
            console.log('Keybase : ', datas['keybase']);
            // Keybase
            if (this.isModuleParamRunTaskExec('keybase', datas['keybase'], 'User', 100)) {
                this.showToast('info', 'Keybase', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('keybase', {username: datas['keybase'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'keybase', datas['keybase']),
                               () => console.log('Completed Keybase'),
                );
            }
        }

        // Evaluation of datas
        if (datas['username'] !== '') {
            console.log('Username : ', datas['username']);
            // // Sherlock (Temporary disable)
            // if (this.isModuleParamRunTaskExec('sherlock', datas['username'], 'User', 100)) {
            //     this.showToast('info', 'Sherlock', 'Send information gathering');
            //     this.globalGather['taskresume'][0].PP++;
            //     this.executeRequest$('sherlock', {username: datas['username'], from: 'User'})
            //         .subscribe(this.processResponse,
            //                    // err => console.error('Ops: ', err.message),
            //                    err => this.processRetry(err, 'User', 'sherlock', datas['username']),
            //                    () => console.log('Completed Sherlock'),
            //     );
            // }

            // Dorks
            if (this.isModuleParamRunTaskExec('dorks', datas['username'], 'User', 100)) {
                this.showToast('info', 'Dorks', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('dorks', {username: datas['username'], dorks: '', from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'dorks', datas['username']),
                               () => console.log('Completed Dorks'),
                );
            }
            // Search
            if (this.isModuleParamRunTaskExec('search', datas['username'], 'User', 100)) {
                this.showToast('info', 'Searchers', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('search', {username: datas['username'], from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'search', datas['username']),
                               () => console.log('Completed Searchers'),
                );
            }
        }

        if (datas['email'] !== '') {
            console.log('Email : ', datas['email']);

            this.email = datas['email'];
            // Split email in username and domain
            this.username = datas['email'].split('@')[0];
            console.log('Username : ', this.username);


            // EmailrepIO
            if (this.isModuleParamRunTaskExec('emailrep', this.email, 'User', 100)) {
                this.showToast('info', 'EmailRepIO', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('emailrep', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'emailrep', this.email),
                               () => console.log('Completed EmailRep'),
                );
            }

            // Leaklookup
            if (this.isModuleParamRunTaskExec('leaklookup', this.email, 'User', 100)) {
                this.showToast('info', 'LeakLookup', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('leaklookup', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'leaklookup', this.email),
                               () => console.log('Completed Leaklookup'),
                );
            }

            // Dorks
            if (this.isModuleParamRunTaskExec('dorks', this.username, 'iKy', 1)) {
                this.showToast('info', 'Dorks', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('dorks', {username: this.username, dorks: '', from: 'iKy'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'iKy', 'dorks', this.username),
                               () => console.log('Completed Dorks'),
                );
            }

            // Search
            if (this.isModuleParamRunTaskExec('search', this.username, 'iKy', 1)) {
                this.showToast('info', 'Searchers', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('search', {username: this.username, from: 'iKy'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'iKy', 'search', this.username),
                               () => console.log('Completed Searchers'),
                );
            }

            // Fullcontact
            if (this.isModuleParamRunTaskExec('fullcontact', this.email, 'User', 100)) {
                this.showToast('info', 'Fullcontact', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('fullcontact', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'fullcontact', this.email),
                               () => console.log('Completed Fullcontact'),
                );
            }

            // Peopledatalabs
            if (this.isModuleParamRunTaskExec('peopledatalabs', this.email, 'User', 100)) {
                this.showToast('info', 'Peopledatalabs', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('peopledatalabs', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'peopledatalabs', this.email),
                               () => console.log('Completed Peopledatalabs'),
                );
            }

            // if (datas['linkedin'] == '') {
            //     // Linkedin
            //     if (this.isModuleParamRunTaskExec('linkedin', this.email, 'User', 100)) {
            //         this.showToast('info', 'Linkedin', 'Send information gathering');
            //         this.globalGather['taskresume'][0].PP++;
            //         this.executeRequest$('linkedin', {username: this.email, from: 'User'})
            //                 .subscribe(this.processResponse,
            //                            err => console.error('Ops: ', err.message),
            //                            () => console.log('Completed linkedin')
            //         );
            //     };
            // }

            // Leaks
            if (this.isModuleParamRunTaskExec('leaks', this.email, 'User', 100)) {
                this.showToast('info', 'Leaks (HIBP)', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('leaks', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'leaks', this.email),
                               () => console.log('Completed Leaks (HIBP)'),
                );
            }

            // Darkpass
            if (this.isModuleParamRunTaskExec('darkpass', this.email, 'User', 100)) {
                this.showToast('info', 'Darkpass (Darknet)', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('darkpass', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'darkpass', this.email),
                               () => console.log('Completed Darkpass (Darknet)'),
                );
            }

            // SocialScan
            if (this.isModuleParamRunTaskExec('socialscan', this.email, 'User', 100)) {
                this.showToast('info', 'SocialScan', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('socialscan', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'socialscan', this.email),
                               () => console.log('Completed SocialScan'),
                );
            }

            // // Sherlock (Temporary disable)
            // if (this.isModuleParamRunTaskExec('sherlock', this.username, 'iKy', 1)) {
            //     this.showToast('info', 'Sherlock', 'Send information gathering');
            //     this.globalGather['taskresume'][0].PP++;
            //     this.executeRequest$('sherlock', {username: this.username, from: 'iKy'})
            //         .subscribe(this.processResponse,
            //                    // err => console.error('Ops: ', err.message),
            //                    err => this.processRetry(err, 'iKy', 'sherlock', this.username),
            //                    () => console.log('Completed Sherlock'),
            //     );
            // }

            // Holehe
            if (this.isModuleParamRunTaskExec('holehe', this.email, 'User', 100)) {
                this.showToast('info', 'Holehe', 'Send information gathering');
                this.globalGather['taskresume'][0].PP++;
                this.executeRequest$('holehe', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               // err => console.error('Ops: ', err.message),
                               err => this.processRetry(err, 'User', 'holehe', this.email),
                               () => console.log('Completed Holehe'),
                );
            }

            if (datas['github'] === '') {
                // Github
                if (this.isModuleParamRunTaskExec('github', this.username, 'iKy', 1)) {
                    this.showToast('info', 'Github', 'Send information gathering');
                    this.globalGather['taskresume'][0].PP++;
                    this.executeRequest$('github', {username: this.username, from: 'iKy'})
                        .subscribe(this.processResponse,
                                   // err => console.error('Ops: ', err.message),
                                   err => this.processRetry(err, 'iKy', 'github', this.username),
                                   () => console.log('Completed Github'),
                    );
                }
            }

            if (datas['keybase'] === '') {
                // Keybase
                if (this.isModuleParamRunTaskExec('keybase', this.username, 'iKy', 1)) {
                    this.showToast('info', 'Keybase', 'Send information gathering');
                    this.globalGather['taskresume'][0].PP++;
                    this.executeRequest$('keybase', {username: this.username, from: 'iKy'})
                        .subscribe(this.processResponse,
                                   // err => console.error('Ops: ', err.message),
                                   err => this.processRetry(err, 'iKy', 'keybase', this.username),
                                   () => console.log('Completed Keybase'),
                    );
                }
            }

            if (datas['reddit'] === '') {
                // Reddit
                if (this.isModuleParamRunTaskExec('reddit', this.username, 'iKy', 1)) {
                    this.showToast('info', 'Reddit', 'Send information gathering');
                    this.globalGather['taskresume'][0].PP++;
                    this.executeRequest$('reddit', {username: this.username, from: 'iKy'})
                        .subscribe(this.processResponse,
                                   // err => console.error('Ops: ', err.message),
                                   err => this.processRetry(err, 'iKy', 'reddit', this.username),
                                   () => console.log('Completed Reddit'),
                    );
                }
            }

            if (datas['spotify'] === '') {
                // Spotify
                if (this.isModuleParamRunTaskExec('spotify', this.username, 'iKy', 1)) {
                    this.showToast('info', 'Spotify', 'Send information gathering');
                    this.globalGather['taskresume'][0].PP++;
                    this.executeRequest$('spotify', {username: this.username, from: 'iKy'})
                        .subscribe(this.processResponse,
                                   // err => console.error('Ops: ', err.message),
                                   err => this.processRetry(err, 'iKy', 'spotify', this.username),
                                   () => console.log('Completed Spotify'),
                    );
                }
            }

            if (datas['twitch'] === '') {
                // Twitch
                if (this.isModuleParamRunTaskExec('twitch', this.username, 'iKy', 1)) {
                    this.showToast('info', 'Twitch', 'Send information gathering');
                    this.globalGather['taskresume'][0].PP++;
                    this.executeRequest$('twitch', {username: this.username, from: 'iKy'})
                        .subscribe(this.processResponse,
                                   // err => console.error('Ops: ', err.message),
                                   err => this.processRetry(err, 'iKy', 'twitch', this.username),
                                   () => console.log('Completed Twitch'),
                    );
                }
            }

            if (datas['mastodon'] === '') {
                // Mastodon
                if (this.isModuleParamRunTaskExec('mastodon', this.username, 'iKy', 1)) {
                    this.showToast('info', 'Mastodon', 'Send information gathering');
                    this.globalGather['taskresume'][0].PP++;
                    this.executeRequest$('mastodon', {username: this.username, from: 'iKy'})
                        .subscribe(this.processResponse,
                                   // err => console.error('Ops: ', err.message),
                                   err => this.processRetry(err, 'iKy', 'mastodon', this.username),
                                   () => console.log('Completed Mastodon'),
                    );
                }
            }

        }
    }

    /* Gather Info for comparison */
    public gathererComparison(data: string) {

        let datas = data;
        // Create if dont exist
        if (this.globalGather['taskresume'] == null) {
            // Process PENDING // Process SUCCESS // Process ERROR
            this.globalGather['taskresume'] = [{PP: 0, PS: 0, PE: 0}];
        }
        console.log('====================================================');
        console.log('Gatherer Comparison Datas : ', datas);

        // Evaluation of datas for first account first period (and second)
        if (datas['twitterf'] !== '') {
            console.log('Twitterf : ', datas['twitterf']);
            // Twitter
            this.showToast('info', 'Twitter first Info', 'Send information gathering');
            // this.globalGather['taskresume'][1].PP++;
            this.executeRequest$('twitter_info', {username: datas['twitterf'], from: 'User', module_name: 'twitter_infof'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed Twitter First info'),
            );
            this.showToast('info', 'Twitter first period', 'Tweets from ' + datas['datef_from'] + ' to ' + datas['datef_to'] );
            // this.globalGather['taskresume'][1].PP++;
            this.executeRequest$('twitter_comp', {username: datas['twitterf'],
                                 date_from: datas['datef_from'],
                                 date_to: datas['datef_to'], from: 'User',
                                 module_name: 'twitter_compf'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed Twitter first period'),
            );
            // Evaluation of second period of same account
            if (datas['twitters'] === '' && datas['dates_from'] !== '' && datas['dates_from'] !== 'NaN-NaN-NaN') {
                this.showToast('info', 'Twitter second period', 'Tweets from ' + datas['dates_from'] + ' to ' + datas['dates_to'] );
                // this.globalGather['taskresume'][1].PP++;
                this.executeRequest$('twitter_comp', {username: datas['twitterf'], date_from: datas['dates_from'],
                                     date_to: datas['dates_to'], from: 'User', module_name: 'twitter_comps'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Twitter second period'),
                );
            }
        }

        // Evaluation of datas for second account second period
        if (datas['twitters'] !== '') {
            console.log('Twitters : ', datas['twitters']);
            // Twitter
            this.showToast('info', 'Twitter second Info', 'Send information gathering');
            // this.globalGather['taskresume'][1].PP++;
            this.executeRequest$('twitter_info', {username: datas['twitters'], from: 'User', module_name: 'twitter_infos'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed Twitter second info'),
            );
            this.showToast('info', 'Twitter second period', 'Tweets from ' + datas['dates_from'] + ' to ' + datas['dates_to'] );
            // this.globalGather['taskresume'][1].PP++;
            this.executeRequest$('twitter_comp', {username: datas['twitters'], date_from: datas['dates_from'],
                                 date_to: datas['dates_to'], from: 'User', module_name: 'twitter_comps'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed Twitter second period'),
            );
        }
    }

    // Tasklist Callback
    private processTasklist = (data: any): any => {
        this.globalGather['tasklist'] = data;
        // this.tasklist = data;
        // this.showToast('success', 'Tasklist', 'Process ended');
    }

    private isTaskImplemented(module) {
        let tasklist = this.globalGather['tasklist'].modules;
        for (let indexTasklist in tasklist) {
            if (tasklist[indexTasklist] === module) return true;
        }
        return false;
    }

    private isModuleParamRun(module, param, from) {
        // Validate if module run
        let taskexec = this.globalGather['taskexec'];
        let mustRun = true;
        for (let indexTaskexec in taskexec) {
            if (taskexec[indexTaskexec].module === module &&
                taskexec[indexTaskexec].param === param) {
                mustRun = false;
            }
        }
        return mustRun;
    }

    private isModuleParamRunTaskExec(module, param, from, score) {
        // Validate if module run
        let taskexec = this.globalGather['taskexec'];
        let mustRun = true;

        // Priority
        if (from == 'search') {
            score = 5;
        }


        for (let indexTaskexec in taskexec) {

            // Evaluate module == / param <> / from <> "User"
            if (taskexec[indexTaskexec].module == module && 
                taskexec[indexTaskexec].param != param && 
                from != "User") {
                mustRun = false; // Not run
            } 
            // Evaluate module == / param <> / score > score
            if (taskexec[indexTaskexec].module == module && 
                taskexec[indexTaskexec].param != param && 
                taskexec[indexTaskexec].score > score) {
                mustRun = false; // Not run
            } 
            // Evaluate module
            if (taskexec[indexTaskexec].module == module && 
                taskexec[indexTaskexec].param == param) {
                mustRun = false; // Not run

                // console.log('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
                // console.log('Module :', module);
                // console.log('Param  :', param);
                // console.log('From   :', from);
                // console.log('Score  :', score);
                // console.log('Score Before :', this.globalGather['taskexec'][indexTaskexec].score);

                this.globalGather['taskexec'][indexTaskexec].score = taskexec[indexTaskexec].score + score;
                // console.log('Score After :', this.globalGather['taskexec'][indexTaskexec].score);
                // console.log('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
            } 
        }
        // Evaluate if run
        if (mustRun) {
            this.globalGather['taskexec'].push({'module' : module, 'param' : param,
                 'state' : 'PENDING', 'from' : from, 'score': score});
        }
        return mustRun;
    }

    // Generic Callback
    private processResponse = (data: any): any => {
        this.response = data;
        let module_name = this.response.result[0].module;
        let param = this.response.result[1].param;
        console.log('************************************************************************');
        console.log('Module :', module_name);
        console.log('Param  :', param);
        console.log('************************************************************************');

        // Valitate tasks to exec others
        for (let index in this.response.result) {
            if (this.response.result[index].tasks && this.response.result[index].tasks.length > 0) {
                let tasks = this.response.result[index].tasks;
                for (let indexTask in tasks) {
                    if (this.isTaskImplemented(tasks[indexTask].module)) {
                        console.log('Implemented : ', tasks[indexTask].module);
                        if (this.isModuleParamRunTaskExec(tasks[indexTask].module,
                                                  tasks[indexTask].param,
                                                  module_name, 10)) {
                            // Execute another tasks
                            this.showToast('info', tasks[indexTask].module, 'Send information gathering');
                            this.globalGather['taskresume'][0].PP++;
                            this.executeRequest$(tasks[indexTask].module, {username: tasks[indexTask].param,
                                                 from: module_name})
                                    .subscribe(this.processResponse,
                                               // err => console.error('Ops: ', err.message),
                                               err => this.processRetry(err, module_name, tasks[indexTask].module, tasks[indexTask].param),
                                               () => console.log('Completed' + tasks[indexTask].module),
                            );
                            // Launch Twint if execute Twitter
                            // if (tasks[indexTask].module === 'twitter') {
                            //     if (this.isModuleParamRunTaskExec('twint',
                            //                                       tasks[indexTask].param,
                            //                                       module_name, 10)) {
                            //         console.log('Implemented : ', tasks[indexTask].module, 'Twint', module_name);
                            //         this.showToast('info', 'Twint', 'Send information gathering');
                            //         this.globalGather['taskresume'][0].PP++;
                            //         this.executeRequest$('twint', {username: tasks[indexTask].param, from: module_name})
                            //                 .subscribe(this.processResponse,
                            //                            err => console.error('Ops: ', err.message),
                            //                            () => console.log('Completed Twint'),
                            //         );
                            //     }
                            // }
                        }
                    }
                }
            }
        }

        // Chained process
        // if (module_name === 'twint') {
        if (module_name === 'twitter') {
            let task_id
            for (let indexTaskexec in this.globalGather['taskexec']) {
                // if (this.globalGather['taskexec'][indexTaskexec].module === 'twint') {
                if (this.globalGather['taskexec'][indexTaskexec].module === 'twitter') {
                    task_id = this.globalGather['taskexec'][indexTaskexec].task_id;
                }
            }
            console.log('Launch tweetiment', task_id);
            // Tweetiment
            this.showToast('info', 'Tweetiment', 'Send information gathering');
            this.globalGather['taskresume'][0].PP++;
            this.executeRequest$('tweetiment', {username: param, from: 'User', task_id: task_id })
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed tweetiment'),
            );
        }

        let stateTask = "SUCCESS";
        let stateTooltip = "Success";
        if (data.result[3].raw[0] != undefined && 
            data.result[3].raw[0].status != undefined && 
            data.result[3].raw[0].status.toLowerCase() == "fail") {
            stateTask = "FAILURE";
            stateTooltip = data.result[3].raw[0].traceback;
            // console.warn("ToolTip", stateTooltip);
        }

        this.globalGather['taskresume'][0].PS++;

        if (stateTask == "SUCCESS") {
            this.showToast('success', module_name, 'Gather ended');
            this.globalGather[module_name] = data;
        } else {
            this.showToast('danger', module_name, 'Gather ended');
            // TODO : Remove this?
            this.globalGather[module_name] = data; 
        }

        for (let indexTaskexec in this.globalGather['taskexec']) {
            if (this.globalGather['taskexec'][indexTaskexec].module === module_name &&
                this.globalGather['taskexec'][indexTaskexec].param === param) {

                this.globalGather['taskexec'][indexTaskexec].state = stateTask;
                this.globalGather['taskexec'][indexTaskexec].reason = stateTooltip;
                // console.log('State change..................',stateTask);
                // console.log(this.globalGather[module_name].result[2].validation);

                // Reprocess validation
                if (this.globalGather['taskexec'][indexTaskexec].score > 99) {
                    this.globalGather[module_name].result[2].validation = 'hard';
                } else if (this.globalGather['taskexec'][indexTaskexec].score > 9) {
                    this.globalGather[module_name].result[2].validation = 'soft';
                } else {
                    this.globalGather[module_name].result[2].validation = 'no';
                }

            }
        }

        console.log('Gathered :', this.globalGather);
    }

    // Error Callback : Retry
    private processRetry = (data: any, from_m: any, module_m: any, param: any): any => {
        console.log("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@");
        console.log("Module: ", module_m);
        console.log("Data: ", data.url);
        console.log("Error: ", data);
        // console.log("Slice: ", data.url.slice(-37));
        console.log("Slice: ", data.url.split("/")[4]);
        console.log("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@");

        // let tasks = {"from_m": from_m, "module": module_m, "param": param, "task": data.url.split("/")[4]}
        let url: string = "state/" + data.url.split("/")[4] + "/" + module_m
        // console.log("URL: ", url);
        // this.getRequestResult$(url, tasks)
        //     .subscribe(this.processResponse,
        //                err => this.processRetry(err, from_m, module_m, param),
        //                () => console.log('Completed RETRY - ' + module),
        // );
        // public getRequest$(url: string): Observable<any> {
        this.getRequest$(url)
            .subscribe(valid => this.processStateVal(valid, from_m, module_m, param),
                       err => console.log('Error RETRY - ' + module),
                       () => console.log('Completed RETRY - ' + module),
        );
    }

    private processStateVal = (data: any, from_m: any, module_m: any, param: any): any => {
        console.log("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
        console.log("Module: ", module_m);
        console.log("data: ", data);

        if (data.state == "FAILURE") {
            for (let indexTaskexec in this.globalGather['taskexec']) {
                if (this.globalGather['taskexec'][indexTaskexec].module == module_m && 
                    this.globalGather['taskexec'][indexTaskexec].param == param) {

                    this.globalGather['taskexec'][indexTaskexec].task_id = data.task_id;
                    this.globalGather['taskexec'][indexTaskexec].state = 'FAILURE';
                }
            }
        } else {
            let tasks = {"from_m": from_m, "module": module_m, "param": param, "task": data.task_id}
            let url: string = "result/" + data.task_id
            console.log("URL: ", url);
            console.log("ID:  ", data.task_id);
            this.getRequestResult$(url, tasks)
                .subscribe(this.processResponse,
                           err => this.processRetry(err, from_m, module_m, param),
                           () => console.log('Completed RETRY - ' + module),
            );
        }
        console.log("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++");
        
    }

    // Toaster
    private showToast(type: NbComponentStatus, title: string, body: string) {

        config: ToasterConfig;
        const config = {
            status: type,
            destroyByClick: true,
            duration: 4000,
            position: NbGlobalPhysicalPosition.TOP_RIGHT,
            preventDuplicates: true,
        };
        // const titleContent = title ? `${title}` : '';
            // hasIcon: true,

        this.toastrService.show(
            body,
            title,
            config);
    }

}
