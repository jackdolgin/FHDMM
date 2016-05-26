import numpy as np
import pandas as pd
from utils import softmax
from scipy.optimize import minimize
from matplotlib import cm

class ML(object):
    def __init__(self, df, n_actions, cues=None, bounds=None):
        """The DataFrame df must contain columns 'action' 'reward'.
        and 'cue'.

        model can be 'sample_average' or 'constant_step_size'
        """
        if type(cues) is not tuple:
            raise TypeError('cues must be a tuple')
        self.n_actions = n_actions
        if cues is None:
            if 'cue' in df.columns:
                self.cues = (df['cue'].values[0],)
                print('Using {:d} for the cue.'.format(self.cues[0]))
            else:
                self.cues = (0,)
                df['cue'] = 0
        else:
            self.cues = cues
        if type(cues) is int:
            self.cues = (cues,)
        self.df = df
        self.bounds = bounds

    def neg_log_likelihood(self, alphabeta):
        df = self.df
        alpha, beta = alphabeta
        df = self.df[self.df['cue'].isin(self.cues)]
        actions, rewards = df['action'].values, df['reward'].values
        cues = df['cue'].values
        prob_log = 0
        Q = dict([[cue, np.zeros(self.n_actions)] for cue in self.cues])
        for action, reward, cue in zip(actions, rewards, cues):
            Q[cue][action] += alpha * (reward - Q[cue][action])
            prob_log += np.log(softmax(Q[cue], beta)[action])
        return -prob_log

    def ml_estimation(self):
        bounds = ((0,1), (0,2))
        r = minimize(self.neg_log_likelihood, [0.1,0.1],
                     method='L-BFGS-B',
                     bounds=bounds)
        return r

    def fit_model(self):
        r = self.ml_estimation('Nelder-Mead')
        if r.status != 0:
            print('trying with Powell')
            r = self.ml_estimation('Powell')
        return r

    def plot_ml(self, ax, alpha, beta, alpha_hat, beta_hat):
        from itertools import product
        n = 50
        alpha_max = 0.2
        beta_max = 1.3
        if alpha is not None:
            alpha_max = alpha_max if alpha < alpha_max else 1.1 * alpha
            beta_max = beta_max if beta < beta_max else 1.1 * beta
        if alpha_hat is not None:
            alpha_max = alpha_max if alpha_hat < alpha_max else 1.1 * alpha_hat
            beta_max = beta_max if beta_hat < beta_max else 1.1 * beta_hat
        alphas = np.linspace(0, alpha_max, n)
        betas = np.linspace(0, beta_max, n)
        Alpha, Beta = np.meshgrid(alphas, betas)
        Z = np.zeros(len(Alpha) * len(Beta))
        for i, (a, b) in enumerate(product(alphas, betas)):
            Z[i] = self.neg_log_likelihood((a, b))
        Z.resize((len(alphas), len(betas)))
        ax.contourf(Alpha, Beta, Z.T, 50, cmap=cm.jet)
        if alpha is not None:
            ax.plot(alpha, beta, 'rs', ms=5)
        if alpha_hat is not None:
            ax.plot(alpha_hat, beta_hat, 'r+', ms=10)
        ax.set_xlabel(r'$\alpha$', fontsize=20)
        ax.set_ylabel(r'$\beta$', fontsize=20)
        return

    def plot_single_subject(self, ax, r, subject, cue):
        alpha, beta = r.x
        converged = ('yes', 'no')[r.status]
        cue = ''.join([str(c) for c in self.cues])
        title = 'Subject: {}, cue: {}, converged: {}'.format(subject, cue,
                                                             converged)
        if r.status == 0:
            self.plot_ml(ax, alpha, beta, None, None)
        else:
            self.plot_ml(ax, None, None, None, None)
        ax.set_title(title)