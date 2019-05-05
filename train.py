import os
import time
import torch
import torch.nn as nn
import utils
from torch.autograd import Variable


def instance_bce_with_logits(logits, labels):
    assert logits.dim() == 2

    loss = nn.functional.binary_cross_entropy_with_logits(logits, labels)
    loss *= labels.size(1)
    return loss


def compute_score_with_logits(logits, labels):
    logits = torch.max(logits, 1)[1].data # argmax
    one_hots = torch.zeros(*labels.size()).cuda()
    one_hots.scatter_(1, logits.view(-1, 1), 1)
    scores = (one_hots * labels)
    return scores

def train(model, train_loader, eval_loader, num_epochs, output):
    print("starting training")
    utils.create_dir(output)
    optim = torch.optim.Adamax(model.parameters())
    logger = utils.Logger(os.path.join(output, 'log.txt'))
    best_eval_score = 0
    loss_dist_fn = nn.MSELoss()
    # eval_score, bound = evaluate(model, eval_loader)

    itr = 0
    for epoch in range(num_epochs):
        total_loss = 0
        train_score = 0
        t = time.time()

        for i, (v, b, q, a, word_vec) in enumerate(train_loader):
            itr += 1
            # print("v.size", v.size(), "v.size(0)", v.size(0), "itr", itr)
            v = Variable(v).cuda()
            b = Variable(b).cuda()
            q = Variable(q).cuda()
            a = Variable(a).cuda()
            word_vec = word_vec.cuda()
            # print("a = " , a)
            # print("q = " , q)
            pred, pred_word_vec = model(v, b, q, a)
            # print("pred_word_vec size = ", pred_word_vec.size())
            # print("word_vec size = ", word_vec.size())
            loss_bce = instance_bce_with_logits(pred, a)
            
            loss_dist = loss_dist_fn(pred_word_vec, word_vec)
            # loss_dist = 0
            loss = loss_bce + loss_dist
            loss.backward()
            
            nn.utils.clip_grad_norm_(model.parameters(), 0.25)
            optim.step()
            optim.zero_grad()

            batch_score = compute_score_with_logits(pred, a.data).sum()
            # print("loss", loss.item())
            loss_curr = loss.item() * v.size(0)
            logger.writer.add_scalar('loss/train', loss_curr, itr)
            logger.writer.add_scalar('score/train', batch_score.item(), itr)
            total_loss += loss_curr
            train_score += batch_score
            print('epoch %d: [%d]-> \ttrain_loss: %.5f' % (epoch, i, loss_curr))

        total_loss /= len(train_loader.dataset)
        train_score = 100 * train_score / len(train_loader.dataset)
        model.train(False)
        eval_score, bound = evaluate(model, eval_loader)
        logger.writer.add_scalar('score/eval', eval_score.item(), itr)
        model.train(True)

        print('epoch %d-> \ttrain_loss: %.5f, score: %.5f \teval score: %.5f (%.5f)' % (epoch, total_loss, train_score, 100 * eval_score, 100 * bound))
        logger.write('epoch %d, time: %.2f' % (epoch, time.time()-t))
        logger.write('\ttrain_loss: %.2f, score: %.2f' % (total_loss, train_score))
        logger.write('\teval score: %.2f (%.2f)' % (100 * eval_score, 100 * bound))

        if eval_score > best_eval_score:
            model_path = os.path.join(output, 'model.pth')
            torch.save(model.state_dict(), model_path)
            best_eval_score = eval_score


def evaluate(model, dataloader):
    score = 0
    upper_bound = 0
    num_data = 0
    for v, b, q, a, word_vec in iter(dataloader):
        # v = Variable(v, volatile=True).cuda()
        # b = Variable(b, volatile=True).cuda()
        # q = Variable(q, volatile=True).cuda()
        v = Variable(v).cuda()
        b = Variable(b).cuda()
        q = Variable(q).cuda()
        pred, pred_word_vec = model(v, b, q, None)
        batch_score = compute_score_with_logits(pred, a.cuda()).sum()
        score += batch_score
        upper_bound += (a.max(1)[0]).sum()
        num_data += pred.size(0)

    score = score / len(dataloader.dataset)
    upper_bound = upper_bound / len(dataloader.dataset)
    return score, upper_bound